from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError

from .api import BoardError
from .entity import BaldrickEntity


async def async_setup_entry(hass, entry, async_add_entities):
    # Stop is the sole direct output command; active tests go through PixelTool ownership.
    if entry.runtime_data.data.verified_writes:
        async_add_entities(
            [Stop(entry.runtime_data, "stop_native_test", "Stop native test")]
        )


class Stop(BaldrickEntity, ButtonEntity):
    async def async_press(self):
        b = await self.coordinator.client.snapshot()
        if (
            not b.verified_writes
            or b.settings.get("sync_network_tests")
            or b.state.get("test_sync_host")
        ):
            raise HomeAssistantError(
                "Unknown firmware or Turnip synchronisation; command disabled"
            )
        try:
            await self.coordinator.client.set_test(
                {"test_mode_active": False}, {"test_mode_active": False}
            )
            await self.coordinator.async_request_refresh()
        except BoardError as e:
            raise HomeAssistantError(str(e)) from e
