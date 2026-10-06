from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory

from .entity import BaldrickEntity


async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities(
        [
            Status(c, k, n, d)
            for k, n, d in [
                ("online", "Online", BinarySensorDeviceClass.CONNECTIVITY),
                ("faults", "Reported warnings", BinarySensorDeviceClass.PROBLEM),
                ("test_mode_active", "Native test active", None),
                ("streaming", "Input stream activity", None),
            ]
        ]
    )


class Status(BaldrickEntity, BinarySensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, c, key, name, dc):
        super().__init__(c, key, name)
        self.key = key
        self._attr_device_class = dc

    @property
    def available(self):
        return self.key == "online" or super().available

    @property
    def is_on(self):
        if self.key == "online":
            return self.coordinator.last_update_success
        s = self.coordinator.data.state
        if self.key == "faults":
            return bool(s["ui_messages"]) if "ui_messages" in s else None
        if self.key == "streaming":
            v = s.get("streaming")
            return (
                any(v.get(k) for k in ("ddp_sources", "sacn_sources", "artnet_sources"))
                if v is not None
                else None
            )
        return s.get(self.key)
