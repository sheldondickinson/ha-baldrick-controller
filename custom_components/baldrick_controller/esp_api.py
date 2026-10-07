"""PixelTool ESP destination protocol; credentials remain server-side."""

from dataclasses import dataclass

from .api import BaldrickClient, BoardError


@dataclass
class EspSnapshot:
    raw: dict

    @property
    def identity(self):
        return self.raw["id"]

    @property
    def model(self):
        return "PixelTool ESP32-C6"

    @property
    def firmware(self):
        return [self.raw["firmware"]]

    @property
    def pixel_output(self):
        return self.raw["api"] == "pixeltool-ddp-v1" and self.firmware == ["0.2.0"]

    @property
    def settings(self):
        return {
            "hostname": "PixelTool ESP32-C6",
            "sync_network_tests": 0,
            "gpio": self.raw["gpio"],
            "brightness_cap": self.raw["brightness_cap"],
            "ports": [
                {
                    "port_type": "pixel",
                    "models": [
                        {
                            "name": "Portable pixel output",
                            "num_channels": self.raw["capacity"] * 3,
                            "start_channel": 0,
                            "colour_order": self.raw["colour_order"],
                        }
                    ],
                }
            ],
        }

    @property
    def state(self):
        return {
            "board_id": self.identity,
            "board_model": self.model,
            "test_mode_active": self.raw["standalone_active"],
            "fx_state": False,
            "test_sync_host": "",
            "receiver_owned": self.raw["owned"],
            "streaming": {"ddp_sources": [], "sacn_sources": [], "artnet_sources": []},
        }


class EspClient(BaldrickClient):
    def __init__(self, host, session, pin=None, expected_id=None):
        super().__init__(host, session)
        self.pin = pin
        self.expected_id = expected_id

    async def snapshot(self):
        import re

        data = await self._request("api/receiver")
        if (
            not isinstance(data, dict)
            or data.get("api") != "pixeltool-ddp-v1"
            or not re.fullmatch(r"[a-f0-9]{12}", str(data.get("id", "")))
            or type(data.get("capacity")) is not int
            or data.get("capacity") != 1000
            or data.get("ddp_port") != 4048
            or data.get("colour_order")
            not in ("RGB", "RBG", "GRB", "GBR", "BRG", "BGR")
            or type(data.get("brightness_cap")) is not int
            or not 1 <= data["brightness_cap"] <= 30
            or type(data.get("gpio")) is not int
            or data["gpio"] not in (0, 1, 2, 3, 18, 19, 20, 23)
            or any(
                type(data.get(k)) is not bool
                for k in ("owned", "standalone_active", "stream_active")
            )
            or not isinstance(data.get("firmware"), str)
        ):
            raise BoardError("Not a supported PixelTool ESP receiver")
        if self.expected_id and data["id"] != self.expected_id:
            raise BoardError("ESP identity changed")
        return EspSnapshot(data)

    async def command(self, op, token=None, count=None):
        import asyncio

        import aiohttp

        if not self.pin:
            raise BoardError("ESP destination needs its private access PIN")
        data = {"op": op, "pin": self.pin}
        if token:
            data["token"] = token
        if count is not None:
            data["count"] = str(count)
        try:
            async with self.session.post(
                f"http://{self.host}/api/receiver",
                data=data,
                timeout=aiohttp.ClientTimeout(total=5),
                allow_redirects=False,
            ) as response:
                if response.status == 409 and op == "release":
                    current = await self.snapshot()
                    if (
                        not current.raw["owned"]
                        and not current.raw["standalone_active"]
                    ):
                        return current.raw
                response.raise_for_status()
                result = await response.json()
                return result
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
            raise BoardError(
                "ESP receiver command failed; no automatic retry"
            ) from None
