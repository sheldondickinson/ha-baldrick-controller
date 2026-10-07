"""Verified identity config flow and host reconfiguration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BaldrickClient, BoardError
from .const import DOMAIN


class BaldrickFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    VERSION = 1

    async def _probe(self, data):
        return await BaldrickClient(
            data["host"], async_get_clientsession(self.hass)
        ).snapshot()

    async def async_step_zeroconf(self, discovery_info):
        from aiohttp import ClientError, ClientTimeout

        config = self.hass.data.get(DOMAIN, {}).get("pixeltool_config")
        if not config:
            import json
            from pathlib import Path

            try:
                path = Path(self.hass.config.path("baldrick_pixeltool.json"))
                config = json.loads(
                    await self.hass.async_add_executor_job(path.read_text)
                )
            except (OSError, ValueError):
                return self.async_abort(reason="cannot_connect")
        try:
            async with async_get_clientsession(self.hass).post(
                config["url"] + "/api",
                json={
                    "op": "destination_discovery",
                    "data": {"host": discovery_info.host},
                },
                headers={"Authorization": "Bearer " + config["token"]},
                timeout=ClientTimeout(total=10),
                allow_redirects=False,
            ) as response:
                response.raise_for_status()
                await response.json()
        except (ClientError, TimeoutError, ValueError):
            return self.async_abort(reason="cannot_connect")
        return self.async_abort(reason="pixeltool_destination_found")

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input:
            try:
                board = await self._probe(user_input)
                await self.async_set_unique_id(board.identity)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=board.settings.get("hostname", board.model),
                    data={"host": user_input["host"], "board_id": board.identity},
                )
            except (BoardError, ValueError):
                errors["base"] = "cannot_connect"
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("host"): str}),
            errors=errors,
        )

    async def async_step_integration_discovery(self, discovery_info):
        try:
            self._discovered_host = discovery_info["host"]
            board = await self._probe(discovery_info)
            await self.async_set_unique_id(board.identity)
            self._abort_if_unique_id_configured()
            self.context["title_placeholders"] = {
                "name": board.settings.get("hostname", board.model)
            }
        except (BoardError, ValueError):
            return self.async_abort(reason="cannot_connect")
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input=None):
        if user_input is not None:
            return await self.async_step_user({"host": self._discovered_host})
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={"host": self._discovered_host},
        )

    async def async_step_reconfigure(self, user_input=None):
        entry = self._get_reconfigure_entry()
        errors = {}
        if user_input:
            try:
                board = await self._probe(user_input)
                if board.identity != entry.unique_id:
                    errors["base"] = "wrong_device"
                else:
                    self.hass.config_entries.async_update_entry(
                        entry, data={**entry.data, "host": user_input["host"]}
                    )
                    return self.async_abort(reason="reconfigure_successful")
            except (BoardError, ValueError):
                errors["base"] = "cannot_connect"
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {vol.Required("host", default=entry.data["host"]): str}
            ),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return OptionsFlow()


class OptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "poll_interval",
                        default=self.config_entry.options.get("poll_interval", 15),
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
                }
            ),
        )
