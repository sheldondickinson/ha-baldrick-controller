from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class BaldrickEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key, name):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_{key}"
        self._attr_name = name

    @property
    def device_info(self):
        b = self.coordinator.data
        return DeviceInfo(
            identifiers={(DOMAIN, b.identity)},
            manufacturer="ILightThat",
            name=b.settings.get("hostname", b.model),
            model=b.model,
            sw_version=" / ".join(b.firmware) or None,
            configuration_url=f"http://{self.coordinator.client.host}/",
        )
