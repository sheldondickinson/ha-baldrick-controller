from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfInformation,
    UnitOfTemperature,
    UnitOfTime,
)

from .entity import BaldrickEntity

SPECS = [
    ("uptime", "Uptime", UnitOfTime.SECONDS, SensorDeviceClass.DURATION),
    ("frame_rate", "Frame rate", "fps", None),
    (
        "ram_available",
        "Available memory",
        UnitOfInformation.BYTES,
        SensorDeviceClass.DATA_SIZE,
    ),
    ("oom_count", "Out of memory count", None, None),
]


async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    entities = [Value(c, k, n, u, d) for k, n, u, d in SPECS if k in c.data.state]
    for i in range(len(c.data.state.get("temperature", []))):
        entities.append(
            Value(
                c,
                f"temperature_{i}",
                f"Temperature {i + 1}",
                UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE,
            )
        )
    for key in ("test_pattern", "test_brightness", "network_throughput"):
        if key in c.data.state:
            entities.append(
                Value(
                    c,
                    key,
                    key.replace("_", " ").title(),
                    "%" if key == "test_brightness" else None,
                )
            )
    for protocol in ("ddp", "sacn", "artnet"):
        for suffix in ("recvd", "dropped"):
            if protocol + "_" + suffix in c.data.state.get("streaming", {}):
                entities.append(
                    Value(
                        c,
                        protocol + "_" + suffix,
                        protocol.upper() + " packets " + suffix,
                    )
                )
    entities += [
        Value(
            c, "last_seen", "Last successful contact", None, SensorDeviceClass.TIMESTAMP
        ),
        Value(c, "firmware", "Firmware"),
        Value(c, "warnings", "Warnings"),
    ]
    for i, port in enumerate(c.data.settings["ports"]):
        entities.append(
            Value(
                c,
                f"port_{i}",
                f"{'DMX universe (shared connectors)' if port['port_type'] == 'dmx' else 'Port ' + str(i + 1)} configuration",
            )
        )
    async_add_entities(entities)


class Value(BaldrickEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, c, key, name, unit=None, device_class=None):
        super().__init__(c, key, name)
        self.key = key
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        if key.startswith("temperature_") or key == "frame_rate":
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def available(self):
        return self.key == "last_seen" or super().available

    @property
    def native_value(self):
        b = self.coordinator.data
        if self.key == "last_seen":
            return self.coordinator.last_seen
        if self.key == "firmware":
            return " / ".join(b.firmware) or None
        if self.key == "warnings":
            return len(b.state["ui_messages"]) if "ui_messages" in b.state else None
        if self.key.startswith("temperature_"):
            i = int(self.key.split("_")[1])
            values = b.state.get("temperature", [])
            return values[i] if i < len(values) else None
        if self.key.startswith("port_"):
            i = int(self.key.split("_")[1])
            ports = b.settings.get("ports", [])
            return (
                sum(m["num_channels"] for m in ports[i].get("models", []))
                if i < len(ports)
                else None
            )
        if self.key in b.state.get("streaming", {}):
            return b.state["streaming"].get(self.key)
        return b.state.get(self.key)

    @property
    def extra_state_attributes(self):
        if self.key.startswith("port_"):
            i = int(self.key.split("_")[1])
            p = self.coordinator.data.settings["ports"][i]
            return {
                "port_type": p["port_type"],
                "models": p.get("models", []),
                "ddp_start_address": self.coordinator.data.settings.get(
                    "start_address"
                ),
                "unit_description": "configured channels; not measured current or power",
            }
        if self.key == "warnings":
            return {"messages": self.coordinator.data.state.get("ui_messages", [])}
        return None
