import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import BoardError
from .const import DOMAIN


class BaldrickCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, client):
        super().__init__(
            hass,
            logging.getLogger(__name__),
            name="Baldrick Controller",
            config_entry=entry,
            update_interval=timedelta(seconds=entry.options.get("poll_interval", 15)),
        )
        self.client = client
        self.last_seen = None
        self.failures = 0
        self.base_interval = entry.options.get("poll_interval", 15)

    async def _async_update_data(self):
        try:
            data = await self.client.snapshot()
            if data.identity != self.config_entry.unique_id:
                raise BoardError("Address now belongs to a different board")
            # Turnip buddy advertisements are verified by HTTP before a UI prompt.
            known = {
                e.unique_id for e in self.hass.config_entries.async_entries(DOMAIN)
            }
            for buddy in data.state.get("buddies") or []:
                if not isinstance(buddy, dict) or not buddy.get("board_id"):
                    continue
                if buddy.get("board_id") not in known and buddy.get("ip"):
                    known.add(buddy["board_id"])
                    self.hass.async_create_task(
                        self.hass.config_entries.flow.async_init(
                            DOMAIN,
                            context={"source": "integration_discovery"},
                            data={"host": buddy["ip"]},
                        )
                    )
            self.last_seen = dt_util.utcnow()
            self.failures = 0
            self.update_interval = timedelta(seconds=self.base_interval)
            return data
        except BoardError as e:
            self.failures += 1
            self.update_interval = timedelta(
                seconds=min(300, self.base_interval * 2 ** min(self.failures, 4))
            )
            raise UpdateFailed(str(e)) from e
