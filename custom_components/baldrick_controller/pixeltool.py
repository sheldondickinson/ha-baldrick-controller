"""Authenticated HA API bridge; companion credential remains server-side."""

import json
from pathlib import Path

from aiohttp import ClientError, ClientTimeout, web
from homeassistant.components import frontend
from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers.aiohttp_client import async_get_clientsession


class PixelToolView(HomeAssistantView):
    url = "/api/baldrick_controller/pixeltool"
    name = "api:baldrick_controller:pixeltool"
    requires_auth = True

    def __init__(self, hass, config):
        self.hass = hass
        self.config = config

    async def post(self, request):
        if not request["hass_user"].is_admin:
            raise web.HTTPForbidden()
        data = await request.json()
        try:
            async with async_get_clientsession(self.hass).post(
                self.config["url"] + "/api",
                json=data,
                headers={"Authorization": "Bearer " + self.config["token"]},
                timeout=ClientTimeout(total=35),
                allow_redirects=False,
            ) as r:
                result = await r.json()
                return web.json_response(result, status=r.status)
        except (ClientError, TimeoutError):
            return web.json_response(
                {
                    "error": "PixelTool companion unavailable; board monitoring continues"
                },
                status=503,
            )


async def setup_pixeltool(hass):
    p = Path(hass.config.path("baldrick_pixeltool.json"))
    if not await hass.async_add_executor_job(p.exists):
        return
    config = json.loads(await hass.async_add_executor_job(p.read_text))
    hass.http.register_view(PixelToolView(hass, config))
    frontend.async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title="PixelTool",
        sidebar_icon="mdi:led-strip-variant",
        frontend_url_path="pixeltool",
        config={
            "_panel_custom": {
                "name": "baldrick-pixeltool-panel",
                "module_url": "/baldrick_controller_static/pixeltool-panel.js?v=0.1.4",
                "embed_iframe": False,
                "trust_external": False,
            }
        },
        require_admin=True,
    )
