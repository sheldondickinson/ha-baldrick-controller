from .api import redact


async def async_get_config_entry_diagnostics(hass, entry):
    b = entry.runtime_data.data
    return {
        "state": redact(b.state),
        "settings": redact(b.settings),
        "firmware": b.firmware,
        "writes_verified": b.verified_writes,
    }
