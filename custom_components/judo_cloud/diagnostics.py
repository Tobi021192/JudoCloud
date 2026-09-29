"""Diagnostics support for mapping additional legacy cloud registers."""

from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_INDEX, DOMAIN

TO_REDACT = {
    CONF_PASSWORD,
    CONF_USERNAME,
    "serial_number",
    "serialnumber",
    "token",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    devices = await coordinator.client.devices()
    index = int(entry.data.get(CONF_DEVICE_INDEX, 0))
    raw_device = devices[index].raw if 0 <= index < len(devices) else {}
    return async_redact_data(
        {
            "config_entry": entry.as_dict(),
            "decoded": coordinator.data,
            "raw_device": raw_device,
            "salt_estimate_configured": coordinator.salt_tracker.is_configured,
        },
        TO_REDACT,
    )
