"""Data update coordinator for JUDO Cloud."""

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import JudoCloudClient, JudoCloudError, decode_device
from .const import CONF_DEVICE_INDEX, DEFAULT_SCAN_INTERVAL, DOMAIN, MIN_SCAN_INTERVAL
from .salt import JudoSaltTracker


class JudoCloudCoordinator(DataUpdateCoordinator[dict]):
    """Poll one selected JUDO device."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: JudoCloudClient,
        salt_tracker: JudoSaltTracker,
    ) -> None:
        interval = max(MIN_SCAN_INTERVAL, int(entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)))
        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )
        self.entry = entry
        self.client = client
        self.salt_tracker = salt_tracker

    async def _async_update_data(self) -> dict:
        try:
            devices = await self.client.devices()
            index = int(self.entry.data.get(CONF_DEVICE_INDEX, 0))
            if index >= len(devices):
                raise UpdateFailed("Das ausgewählte JUDO-Gerät ist nicht mehr vorhanden")
            return decode_device(devices[index].raw)
        except JudoCloudError as err:
            raise UpdateFailed(str(err)) from err
