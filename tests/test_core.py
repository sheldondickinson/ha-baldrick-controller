import asyncio
import json
import struct
import subprocess
from pathlib import Path

import pytest

from custom_components.baldrick_controller.api import (
    BaldrickClient,
    Snapshot,
    redact,
    validate_host,
)
from pixeltool.models import PALETTE, Library, import_model, validate_checkpoints
from pixeltool.output import configured_outputs, mapped_chunks, mapping, packets
from pixeltool.render import pusher, tools
from pixeltool.server import Engine

FIX = Path(__file__).parent / "fixtures"


def board(i=11):
    return Snapshot(
        json.loads((FIX / f"{i}-system_state.json").read_text()),
        json.loads((FIX / f"{i}-settings.json").read_text()),
    )


def model(n=10):
    return import_model(
        (
            '<custommodel name="test" CustomModel="'
            + ",".join(map(str, range(1, n + 1)))
            + '"/>'
        ).encode()
    )


@pytest.mark.parametrize(
    "i,ports,pixel", [(11, 8, True), (12, 8, True), (13, 1, False), (14, 17, True)]
)
def test_real_capabilities(i, ports, pixel):
    b = board(i)
    assert b.verified_writes
    assert b.pixel_output == pixel
    assert len(b.settings["ports"]) == ports


def test_unknown_firmware_reads_only():
    b = board()
    b.state["ota"]["updatable"][0]["current_firmware_version"] = "v999"
    assert b.identity
    assert not b.pixel_output
    assert not b.verified_writes


@pytest.mark.parametrize(
    "host",
    [
        "http://example.com",
        "127.0.0.1",
        "0.0.0.0",
        "224.0.0.1",
        "bad/host",
        "192.168.999.1",
        "host:80",
    ],
)
def test_host_validation(host):
    with pytest.raises(ValueError):
        validate_host(host)


def test_redaction():
    d = redact(
        {
            "password": "secret",
            "network": {"ip_address": "private"},
            "board_id": "abc",
            "firmware": "v3",
        }
    )
    assert "secret" not in str(d) and "private" not in str(d) and d["firmware"] == "v3"


@pytest.mark.parametrize("size", [1, 3, 1439, 1440, 1441, 4500])
def test_ddp_boundaries(size):
    data = bytes(i % 256 for i in range(size))
    p = list(packets(data, offset=123, sequence=15))
    assert b"".join(x[10:] for x in p) == data
    for i, x in enumerate(p):
        flags, seq, typ, dest, offset, length = struct.unpack("!BBBBIH", x[:10])
        assert flags == (0x41 if i == len(p) - 1 else 0x40)
        assert offset == 123 + i * 1440
        assert length == len(x) - 10
        assert dest == 1
        assert 1 <= seq <= 15
        assert len(x) <= 1450


def test_mapping_ports_offsets_overlap_and_first():
    b = board()
    m = model(20)
    instance = {
        "id": "a",
        "board_id": b.identity,
        "first": 5,
        "segments": [
            {"port": 1, "start_pixel": 599, "node": 5, "count": 2},
            {"port": 2, "start_pixel": 1, "node": 7, "count": 14},
        ],
    }
    t = mapping(b, instance, m)
    assert t[0] == (5, 1794)
    assert t[2] == (7, 1800)
    assert mapped_chunks([(1, 2, 3)] * 20, t) == [(1794, bytes([1, 2, 3]) * 16)]
    with pytest.raises(ValueError):
        mapping(b, instance, m, [{**instance, "id": "b"}])
    instance["segments"][0]["count"] = 3
    with pytest.raises(ValueError):
        mapping(b, instance, m)


def test_dmx_pixel_output_blocked():
    with pytest.raises(ValueError):
        configured_outputs(board(13))


def test_unverified_layout_blocked():
    b = board()
    b.settings["ports"][0]["models"][0]["grouping"] = 2
    with pytest.raises(ValueError):
        configured_outputs(b)


@pytest.mark.parametrize(
    "raw",
    [
        b'<!DOCTYPE a [<!ENTITY x SYSTEM "file:///etc/passwd">]><custommodel CustomModel="&x;"/>',
        b'<model DisplayAs="Tree"/>',
        b'<custommodel CustomModel="1,1"/>',
        b'<custommodel CustomModel="1,3"/>',
    ],
)
def test_unsafe_and_unsupported_xml(raw):
    with pytest.raises(Exception):
        import_model(raw)


def test_library_roundtrip_and_instance_integrity(tmp_path):
    library = Library(tmp_path / "library.sqlite3")
    m = model()
    library.save("models", m, b"source")
    points = validate_checkpoints(
        [
            {"node": 1, "colour": 0},
            {"node": 6, "colour": 1, "label": "Suggested", "confirmed": False},
        ],
        10,
    )
    assert points[0]["end"] == 5
    m["checkpoints"] = points
    library.save("models", m)
    library.save("instances", {"id": "a", "model_id": m["id"], "progress": {"node": 6}})
    library.db.close()
    library = Library(tmp_path / "library.sqlite3")
    assert library.get("models", m["id"])["checkpoints"][1]["node"] == 6
    with pytest.raises(ValueError):
        library.remove("models", m["id"])
    library.remove("instances", "a")
    library.remove("models", m["id"])
    assert not library.list("models")


def test_tool_behaviours():
    s = {"mode": 1, "level": 12, "cap": 12, "per": 5, "strands": 2, "tail": 3}
    assert tools(20, s, 5, 500) == (0, 0, 12)
    assert tools(20, s, 13, 500) == (12, 0, 0)
    assert tools(20, s, 12, 500) == (12, 0, 12)
    s = {"mode": 3, "level": 12, "node": 5}
    assert tools(20, s, 4, 500) == (12, 0, 0)
    assert tools(20, s, 5, 500) == (12, 12, 12)
    assert tools(20, s, 6, 500) == (0, 0, 12)
    assert tools(20, {"mode": 5, "level": 12, "start": 4, "finish": 6}, 6, 500) == (
        12,
        12,
        12,
    )


@pytest.mark.asyncio
async def test_session_expiry_blackout_restart(tmp_path):
    e = Engine(Library(tmp_path / "db"), [], None)
    assert not e.armed
    e.owner = "owner"
    e.deadline = 0
    e.armed = True
    e.model = model()
    e.translation = [(1, 0)]
    calls = []
    e.send = lambda c: calls.append(c)
    task = asyncio.create_task(e.loop())
    await asyncio.sleep(0.4)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert (
        not e.armed
        and e.owner is None
        and len(calls) == 5
        and all(all(rgb == (0, 0, 0) for rgb in c) for c in calls)
    )
    with pytest.raises(ValueError):
        e.require_owner("wrong")
    e.sock.close()


def test_pusher_js_parity():
    m = model(20)
    m["checkpoints"] = validate_checkpoints(
        [{"node": 1, "colour": 0}, {"node": 5, "colour": 2}, {"node": 13, "colour": 5}],
        20,
    )
    cases = []
    for mode in range(7):
        for level in [1, 12, 32, 64]:
            for first in [1, 5, 13]:
                for pulse in [False, True]:
                    s = {
                        "model": 0,
                        "mode": mode,
                        "run": 1,
                        "node": 7,
                        "level": level,
                        "cap": level,
                        "first": first,
                        "enabled": True,
                    }
                    cases.append(
                        {
                            "data": {
                                "models": [m],
                                "palette": [{"rgb": p} for p in PALETTE],
                            },
                            "state": s,
                            "pulse": pulse,
                        }
                    )
    code = "const {pixelRGB}=require('./pixeltool/static/colour.js');let s='';process.stdin.on('data',x=>s+=x);process.stdin.on('end',()=>process.stdout.write(JSON.stringify(JSON.parse(s).map(c=>Array.from({length:20},(_,i)=>pixelRGB(c.data,c.state,i+1,c.pulse))))));"
    result = json.loads(
        subprocess.check_output(["node", "-e", code], input=json.dumps(cases).encode())
    )
    for c, colours in zip(cases, result):
        assert colours == [
            list(pusher(m, c["state"], n, c["pulse"])) for n in range(1, 21)
        ]


@pytest.mark.asyncio
async def test_fragmented_http_and_missing_fields():
    from aiohttp import ClientSession, web

    calls = []

    async def endpoint(request):
        calls.append(request.path)
        data = board().state if request.path == "/system_state" else board().settings
        raw = json.dumps(data).encode()
        resp = web.StreamResponse(headers={"Content-Type": "application/json"})
        await resp.prepare(request)
        for i in range(0, len(raw), 17):
            await resp.write(raw[i : i + 17])
            await asyncio.sleep(0)
        await resp.write_eof()
        return resp

    app = web.Application()
    app.router.add_get("/{path}", endpoint)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    async with ClientSession() as session:
        c = BaldrickClient("board.local", session)
        # Route a trusted fixture connection without broadening production host input.
        original = c.session.request

        def request(method, url, **kwargs):
            return original(
                method,
                url.replace("http://board.local", f"http://127.0.0.1:{port}"),
                **kwargs,
            )

        c.session.request = request
        data = await c.snapshot()
        assert data.identity == board().identity
        assert calls == ["/system_state", "/settings"]
    await runner.cleanup()


def test_checkpoint_starts_distinct_from_guide_ends():
    m = model(10)
    m["checkpoints"] = validate_checkpoints(
        [{"node": 1, "colour": 0}, {"node": 6, "colour": 1}], 10
    )
    assert pusher(m, {"mode": 0, "level": 12, "first": 1}, 6, True) != pusher(
        m, {"mode": 0, "level": 12, "first": 1}, 5, True
    )
    assert tools(10, {"mode": 2, "level": 12, "node": 2, "ends": [5]}, 5, 500) == (
        12,
        0,
        0,
    )
    assert tools(10, {"mode": 2, "level": 12, "node": 2, "ends": [5]}, 6, 500) == (
        0,
        0,
        12,
    )


def test_tools_cpp_parity(tmp_path):
    out = tmp_path / "parity"
    subprocess.run(
        [
            "c++",
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-fsanitize=address,undefined",
            "tests/parity.cpp",
            "-o",
            str(out),
        ],
        check=True,
    )
    rows = subprocess.check_output([str(out)], text=True).splitlines()
    k = 0
    for mode in range(13):
        for tick in [0, 300, 600, 1200, 5000]:
            # Firmware walk uses externally updated selected pixel; compare static indicator.
            for n in range(1, 51):
                s = {
                    "mode": 3 if mode == 4 else mode,
                    "node": 15,
                    "start": 10,
                    "finish": 20,
                    "per": 10,
                    "strands": 3,
                    "tail": 5,
                    "ends": [10, 30],
                    "level": 12,
                }
                # Use the firmware supplied pulse exactly for parity (animation cadence tested separately).
                rgb = tools(50, s, n, tick)
                assert rows[k] == ",".join(map(str, rgb))
                k += 1


@pytest.mark.asyncio
async def test_companion_auth_ownership_and_error_paths(tmp_path, monkeypatch):
    from aiohttp import ClientSession, web

    from pixeltool.server import make_app

    p = tmp_path / "private.json"
    p.write_text(json.dumps({"token": "synthetic-test-secret", "boards": []}))
    monkeypatch.setenv("PIXELTOOL_CONFIG", str(p))
    monkeypatch.setenv("PIXELTOOL_DB", str(tmp_path / "db.sqlite3"))
    app = await make_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    url = f"http://127.0.0.1:{port}/api"
    async with ClientSession() as http:
        async with http.post(url, json={"op": "library"}) as r:
            assert r.status == 401
        headers = {"Authorization": "Bearer synthetic-test-secret"}

        async def call(op, data={}, session=None):
            async with http.post(
                url, json={"op": op, "data": data, "session": session}, headers=headers
            ) as r:
                return r.status, await r.json()

        code, result = await call("claim")
        assert code == 200 and result["armed"] is False
        owner = result["session"]
        code, _ = await call("claim")
        assert code == 400
        code, _ = await call("arm", {"external_output_stopped": True}, owner)
        assert code == 400
        code, _ = await call("upload", {"xml": "PCFET0NUWVBFIGE+PGMvPg=="}, owner)
        assert code == 400
        code, _ = await call("release", session=owner)
        assert code == 200
        code, result = await call("status")
        assert code == 200 and not result["armed"] and not result["session_active"]
    await runner.cleanup()


@pytest.mark.asyncio
async def test_native_restore_failure_still_blackouts(tmp_path, monkeypatch):
    import pixeltool.server as server
    from custom_components.baldrick_controller.api import BoardError

    class FailedClient:
        def __init__(self, *args):
            pass

        async def set_test(self, *args):
            raise BoardError("Synthetic timeout")

    monkeypatch.setattr(server, "BaldrickClient", FailedClient)
    e = Engine(
        Library(tmp_path / "db"), [{"id": "fixture", "host": "board.local"}], None
    )
    e.instance = {"board_id": "fixture"}
    e.model = model()
    e.translation = [(1, 0)]
    e.native_active = True
    calls = []
    e.send = calls.append
    with pytest.raises(BoardError):
        await e.stop()
    assert not e.native_active and not e.armed
    assert len(calls) == 5 and all(all(c == (0, 0, 0) for c in f) for f in calls)
    e.sock.close()


def test_missing_optional_firmware_does_not_enable_writes():
    b = board()
    b.state["ota"] = None
    assert b.firmware == [] and not b.verified_writes
    assert b.state.get("voltage") is None


@pytest.mark.asyncio
async def test_timeout_is_bounded_and_not_retried():
    from custom_components.baldrick_controller.api import BoardError

    class TimeoutSession:
        def __init__(self):
            self.calls = 0

        def request(self, method, url, **kwargs):
            self.calls += 1
            assert kwargs["timeout"].total == 5
            assert not kwargs["allow_redirects"]
            raise asyncio.TimeoutError()

    session = TimeoutSession()
    client = BaldrickClient("board.local", session)
    with pytest.raises(BoardError, match="TimeoutError"):
        await client._request("turnip_test/test_config", {"test_mode_active": False})
    assert session.calls == 1
