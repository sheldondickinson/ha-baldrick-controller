"""Local Turnip API. Interfaces evidenced by board web UI and xLights."""

from __future__ import annotations

import asyncio
import ipaddress
import re
from dataclasses import dataclass
from typing import Any

import aiohttp


class BoardError(Exception):
    """Unavailable or invalid board response."""


def validate_host(host: str) -> str:
    host = host.strip().lower().rstrip(".")
    if not re.fullmatch(r"[a-z0-9][a-z0-9.\-]{0,252}", host):
        raise ValueError("Enter a hostname or IPv4 address without a URL or port")
    try:
        addr = ipaddress.ip_address(host)
        if addr.is_multicast or addr.is_unspecified or addr.is_loopback:
            raise ValueError("Enter a unicast board address")
    except ValueError:
        if re.fullmatch(r"[0-9.]+", host):
            raise ValueError("Invalid board address") from None
    return host


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: (
                "**REDACTED**"
                if any(
                    s in k.lower()
                    for s in (
                        "password",
                        "token",
                        "ssid",
                        "address",
                        "hostname",
                        "gateway",
                        "dns",
                        "board_id",
                        "sources",
                        "host",
                        "name",
                        "url",
                    )
                )
                else redact(v)
            )
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


@dataclass
class Snapshot:
    state: dict
    settings: dict

    @property
    def identity(self):
        return str(self.state["board_id"]).lower()

    @property
    def model(self):
        return self.state["board_model"]

    @property
    def firmware(self):
        ota = self.state.get("ota")
        versions = ota.get("updatable") if isinstance(ota, dict) else None
        return (
            [
                v.get("current_firmware_version", "unknown")
                for v in versions
                if isinstance(v, dict)
            ]
            if isinstance(versions, list)
            else []
        )

    @property
    def verified_writes(self):
        return self.model in (
            "Baldrick 8 Port v1.1",
            "Baldrick17",
            "BaldrickDMX",
        ) and self.firmware == (
            ["v3.8.8", "v3.8.4"] if self.model == "Baldrick17" else ["v3.8.8"]
        )

    @property
    def pixel_output(self):
        return self.verified_writes and self.model in (
            "Baldrick 8 Port v1.1",
            "Baldrick17",
        )


class BaldrickClient:
    def __init__(self, host: str, session: aiohttp.ClientSession):
        self.host = validate_host(host)
        self.session = session
        self.lock = asyncio.Lock()

    async def _request(self, path, payload=None):
        try:
            async with self.session.request(
                "POST" if payload is not None else "GET",
                f"http://{self.host}/{path}",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=5),
                allow_redirects=False,
            ) as r:
                r.raise_for_status()
                if r.content_length and r.content_length > 1048576:
                    raise BoardError("Response too large")
                chunks = bytearray()
                async for chunk in r.content.iter_chunked(16384):
                    chunks.extend(chunk)
                    if len(chunks) > 1048576:
                        raise BoardError("Response too large")
                data = bytes(chunks)
                if payload is not None:
                    return None
                import json

                return json.loads(data)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
            raise BoardError(f"Board request failed: {type(e).__name__}") from None

    async def snapshot(self):
        async with self.lock:
            state = await self._request("system_state")
            if (
                not isinstance(state, dict)
                or not re.fullmatch(r"[a-fA-F0-9]{12}", str(state.get("board_id", "")))
                or not str(state.get("board_model", "")).startswith("Baldrick")
            ):
                raise BoardError("Not a verified Baldrick identity")
            settings = await self._request("settings")
            if not isinstance(settings, dict) or not isinstance(
                settings.get("ports"), list
            ):
                raise BoardError("Unsupported settings response")
            # Credentials are discarded immediately; never retain in runtime data.
            settings = {k: v for k, v in settings.items() if k != "network"}
            return Snapshot(state, settings)

    async def set_test(self, payload, expected):
        async with self.lock:
            await self._request("turnip_test/test_config", payload)
            state = await self._request("system_state")
            if any(state.get(k) != v for k, v in expected.items()):
                raise BoardError("Command readback did not match; no automatic retry")
            return state
