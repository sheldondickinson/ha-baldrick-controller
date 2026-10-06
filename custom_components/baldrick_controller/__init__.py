from homeassistant.const import Platform
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BaldrickClient
from .const import DOMAIN
from .coordinator import BaldrickCoordinator
from .frontend import async_register_frontend
from .pixeltool import setup_pixeltool

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass, config):
    await async_register_frontend(hass)
    await setup_pixeltool(hass)
    return True


async def async_setup_entry(hass, entry):
    c = BaldrickCoordinator(
        hass, entry, BaldrickClient(entry.data["host"], async_get_clientsession(hass))
    )
    await c.async_config_entry_first_refresh()
    entry.runtime_data = c
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(reload_entry))
    return True


async def reload_entry(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
