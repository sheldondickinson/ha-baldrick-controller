import json
import struct

import pytest

from custom_components.baldrick_controller.esp_api import EspSnapshot
from pixeltool.models import Library
from pixeltool.output import configured_outputs
from pixeltool.server import Engine


def snapshot(**extra):
    return EspSnapshot(
        {
            "api": "pixeltool-ddp-v1",
            "firmware": "0.2.0",
            "id": "001122334455",
            "capacity": 1000,
            "ddp_port": 4048,
            "gpio": 2,
            "colour_order": "GRB",
            "brightness_cap": 15,
            "owned": False,
            "standalone_active": False,
            "stream_active": False,
            **extra,
        }
    )


def test_esp_capacity_and_unknown_firmware():
    s = snapshot()
    assert configured_outputs(s)[0]["pixels"] == 1000
    assert s.settings["ports"][0]["models"][0]["colour_order"] == "GRB"
    with pytest.raises(ValueError):
        configured_outputs(snapshot(firmware="unknown"))


def test_esp_dense_frame_and_final_push(tmp_path):
    e = Engine(
        Library(tmp_path / "db"),
        [{"id": "001122334455", "host": "192.0.2.1", "kind": "esp"}],
        None,
    )
    e.board = snapshot()
    e.instance = {"board_id": "001122334455"}
    e.translation = [(1, 1500), (2, 2997)]
    captured = []
    e.sock.close()

    class Socket:
        def sendto(self, data, address):
            captured.append(bytes(data))

    e.sock = Socket()
    e.send([(12, 0, 0), (0, 12, 0)])
    assert [struct.unpack("!BBBBIH", p[:10])[4:6] for p in captured] == [
        (0, 1440),
        (1440, 1440),
        (2880, 120),
    ]
    assert [p[0] for p in captured] == [0x40, 0x40, 0x41]
    body = b"".join(p[10:] for p in captured)
    assert body[:1500] == bytes(1500) and body[1500:1503] == bytes([12, 0, 0])
    assert body[2997:] == bytes([0, 12, 0])


@pytest.mark.asyncio
async def test_esp_arm_lease_and_stop_release(tmp_path):
    e = Engine(Library(tmp_path / "db"), [], None)
    e.selected = "test"
    e.instance = {"board_id": "001122334455"}
    e.board = snapshot()
    e.model = {"count": 2}
    e.translation = [(1, 0), (2, 3)]
    import hashlib

    e.revision = hashlib.sha256(
        json.dumps(e.board.settings, sort_keys=True).encode()
    ).hexdigest()
    calls = []

    class Client:
        async def command(self, op, **data):
            calls.append((op, data))
            return {"token": "synthetic-lease-token"}

    async def get(_):
        return e.board

    e.snapshot = get
    e.client = lambda _: Client()
    e.send = lambda _: None
    await e.arm(True)
    assert e.armed and calls[0] == ("claim", {"count": 2})
    await e.stop()
    assert not e.armed and e.receiver_token is None and calls[-1][0] == "release"
    e.board = snapshot(owned=True)
    with pytest.raises(ValueError, match="Another device"):
        await e.arm(True)
    e.sock.close()
