"""PixelTool companion: durable library, expiring exclusive output sessions."""

from __future__ import annotations

import asyncio
import base64
import contextlib
import hashlib
import hmac
import json
import os
import secrets
import socket
import time
from pathlib import Path
from typing import Any

from aiohttp import ClientSession, web

from custom_components.baldrick_controller.api import BaldrickClient, BoardError

from .models import PALETTE, Library, import_model, validate_checkpoints
from .output import configured_outputs, mapped_chunks, mapping, packets
from .render import frame


class Engine:
    def __init__(self, library, boards, session):
        self.library = library
        self.boards = boards
        self.http = session
        self.source_ip = None
        self.owner = None
        self.deadline = 0.0
        self.native_active = False
        self.native_stop_uncertain = False
        self.native_deadline = 0.0
        self.native_saved = {}
        self.armed = False
        self.state: dict[str, Any] = {
            "tool": "pusher",
            "mode": 0,
            "node": 1,
            "run": 0,
            "first": 1,
            "level": 12,
            "cap": 12,
            "per": 50,
            "strands": 1,
            "tail": 0,
            "start": 1,
            "finish": 50,
            "ends": [],
            "walk_ms": 500,
        }
        self.selected = None
        self.translation = []
        self.board = None
        self.model: dict[str, Any] = {}
        self.instance: dict[str, Any] = {}
        self.revision = None
        self.error = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.lock = asyncio.Lock()
        self.sequence = 1
        self.started = time.monotonic()
        self.last_verified = 0.0

    def status(self):
        return {
            "armed": self.armed,
            "native_active": self.native_active,
            "native_stop_uncertain": self.native_stop_uncertain,
            "session_active": bool(self.owner),
            "expires_in": max(0, int(self.deadline - time.monotonic())),
            "state": self.state,
            "selected": self.selected,
            "error": self.error,
            "output_limitation": "Session ownership excludes other PixelTool sessions only; external DDP senders must be stopped.",
        }

    def require_owner(self, token):
        if (
            not self.owner
            or not hmac.compare_digest(str(token), self.owner)
            or time.monotonic() >= self.deadline
        ):
            raise ValueError("Session absent, expired or owned by another client")

    async def snapshot(self, identity):
        board_config = next((b for b in self.boards if b["id"] == identity), None)
        if not board_config:
            raise ValueError("Unknown registered board")
        b = await BaldrickClient(board_config["host"], self.http).snapshot()
        if b.identity != identity:
            raise ValueError("Board identity changed")
        return b

    async def select(self, instance_id):
        await self.stop()
        instance = self.library.get("instances", instance_id)
        model = self.library.get("models", instance["model_id"])
        b = await self.snapshot(instance["board_id"])
        translated = mapping(b, instance, model, self.library.list("instances"))
        self.selected = instance_id
        self.instance = instance
        self.model = model
        self.board = b
        self.translation = translated
        self.revision = hashlib.sha256(
            json.dumps(b.settings, sort_keys=True).encode()
        ).hexdigest()
        self.state.update(instance.get("progress", {}))
        self.state.update(
            per=min(self.state.get("per", 50), model["count"]),
            finish=min(self.state.get("finish", 50), model["count"]),
            first=instance.get("first", 1),
            node=instance.get("progress", {}).get("node", instance.get("first", 1)),
            run=min(
                instance.get("progress", {}).get("run", 0),
                len(model["checkpoints"]) - 1,
            ),
        )

    def send(self, colours):
        host = next(
            b["host"] for b in self.boards if b["id"] == self.instance["board_id"]
        )
        chunks = mapped_chunks(colours, self.translation)
        all_packets = []
        for offset, data in chunks:
            for packet in packets(data, offset, self.sequence):
                all_packets.append(bytearray(packet))
                self.sequence = self.sequence % 15 + 1
        for i, packet in enumerate(all_packets):
            packet[0] = 0x41 if i == len(all_packets) - 1 else 0x40
            self.sock.sendto(packet, (host, 4048))

    async def native_test(self, pattern, ack):
        if pattern not in (
            "red",
            "green",
            "blue",
            "rainbow",
            "hodgson",
            "model_colours",
        ):
            raise ValueError("Unsupported low-brightness native pattern")
        if (
            len(self.instance.get("segments", [])) != 1
            or self.instance["segments"][0]["start_pixel"] != 1
            or self.instance["segments"][0]["count"] < 50
        ):
            raise ValueError(
                "Native test requires at least 50 identified pixels starting at pixel 1 on one mapped port"
            )
        await self.arm(ack)
        self.armed = False
        client = BaldrickClient(
            next(
                b["host"] for b in self.boards if b["id"] == self.instance["board_id"]
            ),
            self.http,
        )
        b = await client.snapshot()
        self.native_saved = {
            k: b.state[k]
            for k in (
                "test_mode_active",
                "test_pattern",
                "test_brightness",
                "test_ports",
                "test_target",
                "test_dmx_preset",
            )
            if k in b.state
        }
        self.native_active = True
        self.native_deadline = time.monotonic() + 5
        try:
            await client.set_test(
                {
                    "test_mode_active": True,
                    "test_pattern": pattern,
                    "test_brightness": min(5, self.state["cap"] * 100 // 255),
                    "test_ports": str(self.instance["segments"][0]["port"]) + ",",
                    "test_target": "50",
                },
                {"test_mode_active": True, "test_pattern": pattern},
            )
        except BoardError:
            await self.stop()
            raise

    async def stop(self):
        was_armed = self.armed or self.native_active or self.native_stop_uncertain
        self.armed = False
        try:
            if self.native_active or self.native_stop_uncertain:
                self.native_active = False
                client = BaldrickClient(
                    next(
                        b["host"]
                        for b in self.boards
                        if b["id"] == self.instance["board_id"]
                    ),
                    self.http,
                )
                try:
                    await client.set_test(
                        {**self.native_saved, "test_mode_active": False},
                        {"test_mode_active": False},
                    )
                    self.native_stop_uncertain = False
                    if self.error and self.error.startswith(
                        "Native test stop unconfirmed"
                    ):
                        self.error = None
                except BoardError:
                    self.native_stop_uncertain = True
                    self.error = "Native test stop unconfirmed: pixels may remain on. Use the board web interface to stop the test."
                    raise
        finally:
            if was_armed and self.model and self.translation:
                # Complete black frames even if native-test restoration failed.
                for _ in range(5):
                    self.send([(0, 0, 0)] * self.model["count"])
                    await asyncio.sleep(0.05)

    async def arm(self, ack):
        if ack is not True:
            raise ValueError(
                "Confirm suitable load and external xLights/FPP output stopped"
            )
        if not self.selected:
            raise ValueError("Select and validate an instance first")
        b = await self.snapshot(self.instance["board_id"])
        if not b.pixel_output:
            raise ValueError("Current firmware is not verified for pixel output")
        if b.settings.get("sync_network_tests") or b.state.get("test_sync_host"):
            raise ValueError(
                "Turnip test synchronisation enabled; turn it off in the board UI before a test"
            )
        if (
            b.state.get("test_mode_active")
            or b.state.get("fx_state")
            or any(
                b.state.get("streaming", {}).get(k)
                for k in ("ddp_sources", "sacn_sources", "artnet_sources")
            )
        ):
            raise ValueError("Controller has an active test, effect or incoming stream")
        if (
            hashlib.sha256(json.dumps(b.settings, sort_keys=True).encode()).hexdigest()
            != self.revision
        ):
            raise ValueError("Controller configuration changed; reselect mapping")
        self.armed = True
        self.started = time.monotonic()
        self.last_verified = time.monotonic()
        self.error = None
        self.native_stop_uncertain = False

    async def loop(self):
        while True:
            await asyncio.sleep(0.05)
            async with self.lock:
                try:
                    if self.owner and time.monotonic() >= self.deadline:
                        try:
                            await self.stop()
                        finally:
                            self.owner = None
                    if self.native_active and time.monotonic() >= self.native_deadline:
                        await self.stop()
                    if not self.armed:
                        continue
                    if time.monotonic() - self.last_verified >= 5:
                        b = await self.snapshot(self.instance["board_id"])
                        self.last_verified = time.monotonic()
                        sources = [
                            source
                            for key in ("ddp_sources", "sacn_sources", "artnet_sources")
                            for source in b.state.get("streaming", {}).get(key, [])
                        ]
                        if self.source_ip and any(
                            source != self.source_ip for source in sources
                        ):
                            raise ValueError(
                                "External output source appeared; release/takeover required"
                            )
                        if (
                            not b.pixel_output
                            or b.state.get("test_mode_active")
                            or b.settings.get("sync_network_tests")
                            or hashlib.sha256(
                                json.dumps(b.settings, sort_keys=True).encode()
                            ).hexdigest()
                            != self.revision
                        ):
                            raise ValueError(
                                "Board configuration or test state changed"
                            )
                    self.send(
                        frame(
                            self.model,
                            self.state,
                            int((time.monotonic() - self.started) * 1000),
                        )
                    )
                except (ValueError, BoardError, OSError):
                    if not self.native_stop_uncertain:
                        self.error = (
                            "Output stopped: board unavailable or configuration changed"
                        )
                    if self.armed or self.native_active:
                        with contextlib.suppress(BoardError, OSError):
                            await self.stop()


async def make_app():
    config = json.loads(
        Path(
            os.environ.get("PIXELTOOL_CONFIG", "/run/secrets/pixeltool.json")
        ).read_text()
    )
    library = Library(os.environ.get("PIXELTOOL_DB", "/data/pixeltool.sqlite3"))
    http = ClientSession()
    engine = Engine(library, config["boards"], http)
    engine.source_ip = config.get("source_ip")

    @web.middleware
    async def auth(request, handler):
        if request.path == "/health":
            return await handler(request)
        if not hmac.compare_digest(
            request.headers.get("Authorization", ""), "Bearer " + config["token"]
        ):
            raise web.HTTPUnauthorized()
        try:
            return await handler(request)
        except (ValueError, BoardError, KeyError, TypeError) as e:
            return web.json_response({"error": str(e)}, status=400)

    app = web.Application(middlewares=[auth], client_max_size=3 * 1024 * 1024)

    async def health(r):
        return web.json_response(
            {"status": "ok", "armed": engine.armed, "version": "0.1.4"}
        )

    async def api(r):
        data = await r.json()
        op = data.get("op")
        payload = data.get("data", {})
        token = data.get("session")
        async with engine.lock:
            if op == "status":
                return web.json_response(engine.status())
            if op == "boards":
                boards = []
                for b in config["boards"]:
                    try:
                        snap = await engine.snapshot(b["id"])
                        boards.append(
                            {
                                "id": b["id"],
                                "name": snap.settings.get("hostname", snap.model),
                                "model": snap.model,
                                "firmware": snap.firmware,
                                "online": True,
                                "pixel_output": snap.pixel_output,
                                "outputs": configured_outputs(snap)
                                if snap.pixel_output
                                else [],
                                "state": {
                                    k: snap.state.get(k)
                                    for k in [
                                        "frame_rate",
                                        "test_mode_active",
                                        "test_sync_host",
                                    ]
                                },
                            }
                        )
                    except (BoardError, ValueError):
                        boards.append(
                            {
                                "id": b["id"],
                                "name": b.get("name", "Baldrick"),
                                "online": False,
                                "pixel_output": False,
                            }
                        )
                return web.json_response(boards)
            if op == "library":
                return web.json_response(
                    {
                        "models": library.list("models"),
                        "instances": library.list("instances"),
                        "palette": PALETTE,
                    }
                )
            if op == "claim":
                if engine.owner and time.monotonic() < engine.deadline:
                    raise ValueError(
                        "Another session owns output; stop/release there or wait for expiry"
                    )
                await engine.stop()
                engine.owner = secrets.token_urlsafe(32)
                engine.deadline = time.monotonic() + 60
                return web.json_response({"session": engine.owner, **engine.status()})
            if op == "stop":
                await engine.stop()
                return web.json_response(engine.status())
            engine.require_owner(token)
            if op == "heartbeat":
                engine.deadline = time.monotonic() + 60
            elif op == "release":
                await engine.stop()
                engine.owner = None
            elif op == "stop":
                await engine.stop()
            elif op == "select":
                await engine.select(payload["id"])
            elif op == "arm":
                await engine.arm(payload.get("external_output_stopped"))
            elif op == "native_test":
                await engine.native_test(
                    payload.get("pattern"), payload.get("external_output_stopped")
                )
            elif op == "upload":
                await engine.stop()
                raw = base64.b64decode(payload["xml"], validate=True)
                m = import_model(raw)
                library.save("models", m, raw)
                return web.json_response(m)
            elif op == "model_save":
                await engine.stop()
                m = library.get("models", payload["id"])
                m["title"] = str(payload.get("title", m["title"]))[:120]
                if "checkpoints" in payload:
                    m["checkpoints"] = validate_checkpoints(
                        payload["checkpoints"], m["count"]
                    )
                library.save("models", m)
                engine.selected = None
                engine.model = {}
            elif op == "instance_save":
                await engine.stop()
                p = dict(payload)
                p.setdefault("id", secrets.token_hex(16))
                m = library.get("models", p["model_id"])
                b = await engine.snapshot(p["board_id"])
                mapping(b, p, m, library.list("instances"))
                library.save("instances", p)
                engine.selected = None
                engine.model = {}
            elif op == "remove":
                await engine.stop()
                library.remove(payload["kind"], payload["id"])
                engine.selected = None
                engine.model = {}
            elif op == "state":
                if not engine.model:
                    raise ValueError("Select an instance first")
                s = {**engine.state, **payload}
                count = engine.model["count"]
                if s.get("tool") not in ("pusher", "tools"):
                    raise ValueError("Unknown tool")
                ranges = {
                    "mode": (0, 6 if s["tool"] == "pusher" else 12),
                    "node": (1, count),
                    "run": (
                        0,
                        len(engine.model["checkpoints"]) - 1
                        if s["tool"] == "pusher"
                        else len(s["ends"]),
                    ),
                    "first": (1, count),
                    "level": (1, 64),
                    "cap": (1, 76),
                    "per": (1, count),
                    "strands": (1, count),
                    "tail": (0, count),
                    "start": (1, count),
                    "finish": (1, count),
                    "walk_ms": (100, 10000),
                }
                for k, (lo, hi) in ranges.items():
                    if type(s[k]) is not int or not lo <= s[k] <= hi:
                        raise ValueError("Invalid " + k)
                if (
                    s["start"] > s["finish"]
                    or s["per"] * s["strands"] + s["tail"] > count
                    or not isinstance(s["ends"], list)
                    or s["ends"] != sorted(set(s["ends"]))
                    or any(type(n) is not int or not 1 <= n < count for n in s["ends"])
                ):
                    raise ValueError(
                        "Invalid inclusive range, cutter total or guide ends"
                    )
                if s["first"] != engine.state["first"]:
                    await engine.stop()
                    raise ValueError("Edit first model node through instance mapping")
                engine.state = s
                engine.instance["progress"] = dict(s)
                library.save("instances", engine.instance)
            elif op == "mark":
                s = engine.state
                expected = (
                    engine.model["checkpoints"][s["run"]]["node"]
                    if s["tool"] == "pusher"
                    else (s["ends"] + [engine.model["count"]])[
                        min(s["run"], len(s["ends"]))
                    ]
                )
                return web.json_response(
                    {
                        "expected": expected,
                        "selected": s["node"],
                        "difference": s["node"] - expected,
                        "note": "Comparison of selected positions; no physical detection",
                    }
                )
            elif op == "preview":
                return web.json_response(
                    {
                        "colours": frame(
                            engine.model, engine.state, int(payload.get("tick", 0))
                        )
                    }
                )
            else:
                raise ValueError("Unknown operation")
            return web.json_response(engine.status())

    app.router.add_get("/health", health)
    app.router.add_post("/api", api)

    task_key = web.AppKey("output_task", asyncio.Task)

    async def start(app):
        app[task_key] = asyncio.create_task(engine.loop())

    async def cleanup(app):
        app[task_key].cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await app[task_key]
        await engine.stop()
        await http.close()
        engine.sock.close()
        library.db.close()

    app.on_startup.append(start)
    app.on_cleanup.append(cleanup)
    return app


if __name__ == "__main__":
    web.run_app(make_app(), host="0.0.0.0", port=8099, access_log=None)
