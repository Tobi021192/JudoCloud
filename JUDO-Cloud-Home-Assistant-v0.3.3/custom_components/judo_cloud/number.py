"""User-adjustable values for the JUDO salt estimate."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.const import UnitOfMass
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, SALT_TANK_CAPACITY_KG
from .entity import JudoCloudEntity


@dataclass(frozen=True, kw_only=True)
class JudoNumberDescription(NumberEntityDescription):
    """JUDO number description."""

    kind: str


DESCRIPTIONS = (
    JudoNumberDescription(
        key="salt_reference_amount",
        name="Salzmenge nach Befüllung",
        kind="reference",
        native_min_value=1,
        native_max_value=SALT_TANK_CAPACITY_KG,
        native_step=1,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        mode=NumberMode.BOX,
        icon="mdi:shaker-outline",
    ),
    JudoNumberDescription(
        key="salt_use_rate",
        name="Salzverbrauch je m³ Weichwasser",
        kind="rate",
        native_min_value=0.1,
        native_max_value=1.0,
        native_step=0.01,
        native_unit_of_measurement="kg/m³",
        mode=NumberMode.BOX,
        icon="mdi:tune-variant",
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(JudoSaltNumber(coordinator, description) for description in DESCRIPTIONS)


class JudoSaltNumber(JudoCloudEntity, NumberEntity):
    """Configure the baseline or consumption factor for the estimate."""

    def __init__(self, coordinator, description: JudoNumberDescription) -> None:
        self.entity_description = description
        super().__init__(coordinator, description.key)

    @property
    def native_value(self) -> float | None:
        tracker = self.coordinator.salt_tracker
        if self.entity_description.kind == "reference":
            return tracker.reference_amount_kg
        return tracker.use_kg_per_m3

    async def async_set_native_value(self, value: float) -> None:
        tracker = self.coordinator.salt_tracker
        if self.entity_description.kind == "reference":
            soft_water_l = self.coordinator.data.get("soft_water_total")
            if soft_water_l is None:
                raise HomeAssistantError(
                    "Die Weichwassermenge ist derzeit nicht verfügbar. Bitte später erneut versuchen."
                )
            await tracker.async_set_reference(value, int(soft_water_l))
        else:
            await tracker.async_set_use_rate(value)
        self.coordinator.async_update_listeners()
