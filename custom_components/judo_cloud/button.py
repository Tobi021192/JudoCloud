"""Buttons for JUDO Cloud."""

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.exceptions import HomeAssistantError

from .api import JudoCloudError
from .const import CONF_DEVICE_INDEX, DOMAIN, SALT_TANK_CAPACITY_KG
from .entity import JudoCloudEntity

REGENERATION_DESCRIPTION = ButtonEntityDescription(
    key="start_regeneration",
    name="Regeneration starten",
    icon="mdi:autorenew",
)

SALT_REFILL_DESCRIPTION = ButtonEntityDescription(
    key="refill_salt_25kg",
    name="Salz auffüllen (25 kg)",
    icon="mdi:shaker-outline",
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the JUDO action buttons."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [JudoRegenerationButton(coordinator), JudoSaltRefillButton(coordinator)]
    )


class JudoRegenerationButton(JudoCloudEntity, ButtonEntity):
    """Start a regeneration cycle through myJUDO."""

    entity_description = REGENERATION_DESCRIPTION

    def __init__(self, coordinator):
        super().__init__(coordinator, REGENERATION_DESCRIPTION.key)

    async def async_press(self) -> None:
        """Start regeneration and refresh the device data."""
        device_index = int(self.coordinator.entry.data.get(CONF_DEVICE_INDEX, 0))
        try:
            await self.coordinator.client.start_regeneration(device_index)
        except JudoCloudError as err:
            raise HomeAssistantError(f"Regeneration konnte nicht gestartet werden: {err}") from err
        await self.coordinator.async_request_refresh()


class JudoSaltRefillButton(JudoCloudEntity, ButtonEntity):
    """Add one 25 kg bag to the estimated salt inventory."""

    entity_description = SALT_REFILL_DESCRIPTION

    def __init__(self, coordinator):
        super().__init__(coordinator, SALT_REFILL_DESCRIPTION.key)

    async def async_press(self) -> None:
        """Add 25 kg to the estimate and establish a new water baseline."""
        soft_water_l = self.coordinator.data.get("soft_water_total")
        if soft_water_l is None:
            raise HomeAssistantError(
                "Die Weichwassermenge ist derzeit nicht verfügbar. Bitte später erneut versuchen."
            )

        tracker = self.coordinator.salt_tracker
        estimate = tracker.estimate(int(soft_water_l))
        current_kg = estimate.remaining_kg if estimate.remaining_kg is not None else 0.0
        new_amount_kg = min(SALT_TANK_CAPACITY_KG, current_kg + 25.0)
        await tracker.async_set_reference(new_amount_kg, int(soft_water_l))
        self.coordinator.async_update_listeners()
