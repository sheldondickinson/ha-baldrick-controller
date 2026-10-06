"""Isolated coordinator checks on the installed HA runtime; no production database."""

import asyncio
import tempfile
from datetime import timedelta
from types import SimpleNamespace

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.baldrick_controller.api import BoardError, Snapshot
from custom_components.baldrick_controller.coordinator import BaldrickCoordinator


async def main():
    with tempfile.TemporaryDirectory(prefix="baldrick-validation-") as directory:
        hass = HomeAssistant(directory)
        hass.config_entries = SimpleNamespace(async_entries=lambda domain: [])
        entry = SimpleNamespace(
            entry_id="isolated-test",
            unique_id="001122334455",
            options={},
            async_on_unload=lambda callback: None,
        )

        class Client:
            fails = False

            async def snapshot(self):
                if self.fails:
                    raise BoardError("Synthetic offline timeout")
                return Snapshot(
                    {"board_id": entry.unique_id, "board_model": "Baldrick fixture"},
                    {"ports": []},
                )

        client = Client()
        coordinator = BaldrickCoordinator(hass, entry, client)
        await coordinator._async_update_data()
        seen = coordinator.last_seen
        client.fails = True
        for failure in range(1, 7):
            try:
                await coordinator._async_update_data()
                raise AssertionError("Offline read should fail")
            except UpdateFailed:
                pass
            assert coordinator.last_seen == seen
            assert coordinator.update_interval <= timedelta(seconds=300)
            assert coordinator.failures == failure
        client.fails = False
        await coordinator._async_update_data()
        assert coordinator.last_seen >= seen
        assert coordinator.failures == 0
        assert coordinator.update_interval == timedelta(seconds=15)
        print(
            "Installed HA coordinator: offline/backoff/last-seen/recovery passed; isolated scratch state"
        )


asyncio.run(main())
