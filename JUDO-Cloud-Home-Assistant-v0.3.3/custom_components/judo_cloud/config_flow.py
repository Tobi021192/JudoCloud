"""Config flow for JUDO Cloud."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import JudoCloudAuthError, JudoCloudClient, JudoCloudConnectionError
from .const import CONF_DEVICE_INDEX, DOMAIN


class JudoCloudConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up JUDO Cloud using account credentials."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            client = JudoCloudClient(
                async_get_clientsession(self.hass),
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            try:
                devices = await client.devices()
            except JudoCloudAuthError:
                errors["base"] = "invalid_auth"
            except JudoCloudConnectionError:
                errors["base"] = "cannot_connect"
            else:
                if len(devices) == 1:
                    return await self._finish(user_input, devices[0].index, devices[0].serial_number)
                self._login = user_input
                self._devices = devices
                return await self.async_step_device()
        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_device(self, user_input=None):
        if user_input is not None:
            index = int(user_input[CONF_DEVICE_INDEX])
            device = next(device for device in self._devices if device.index == index)
            return await self._finish(self._login, index, device.serial_number)
        choices = {device.index: device.name for device in self._devices}
        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema({vol.Required(CONF_DEVICE_INDEX): vol.In(choices)}),
        )

    async def _finish(self, login: dict, index: int, serial: str):
        await self.async_set_unique_id(serial)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"JUDO {serial}", data={**login, CONF_DEVICE_INDEX: index}
        )

