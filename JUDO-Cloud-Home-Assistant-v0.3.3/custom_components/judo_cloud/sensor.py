"""Useful device and calculated salt sensors for JUDO Cloud."""

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfMass, UnitOfVolume

from .const import DOMAIN
from .entity import JudoCloudEntity


@dataclass(frozen=True, kw_only=True)
class JudoSensorDescription(SensorEntityDescription):
    """JUDO sensor description."""

    salt_key: str | None = None


SENSORS = (
    JudoSensorDescription(
        key="soft_water_total",
        name="Enthärtete Weichwassermenge",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    JudoSensorDescription(
        key="salt_consumption_estimated",
        name="Salzverbrauch geschätzt",
        salt_key="consumed_kg",
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
        icon="mdi:shaker-outline",
    ),
    JudoSensorDescription(
        key="salt_remaining_estimated",
        name="Salzvorrat geschätzt",
        salt_key="remaining_kg",
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:shaker-outline",
    ),
    JudoSensorDescription(
        key="salt_level_estimated",
        name="Salzfüllstand geschätzt",
        salt_key="level_percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:percent",
    ),
    JudoSensorDescription(
        key="salt_range_estimated",
        name="Salzreichweite geschätzt",
        salt_key="range_days",
        native_unit_of_measurement="d",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:calendar-clock",
    ),
    JudoSensorDescription(
        key="regenerations_remaining_estimated",
        name="Verbleibende Regenerationen geschätzt",
        salt_key="regenerations_remaining",
        native_unit_of_measurement="Regenerationen",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:autorenew",
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(JudoCloudSensor(coordinator, description) for description in SENSORS)


class JudoCloudSensor(JudoCloudEntity, SensorEntity):
    """One decoded cloud value."""

    def __init__(self, coordinator, description):
        self.entity_description = description
        super().__init__(coordinator, description.key)

    @property
    def native_value(self):
        if self.entity_description.salt_key is not None:
            estimate = self.coordinator.salt_tracker.estimate(
                self.coordinator.data.get("soft_water_total")
            )
            return getattr(estimate, self.entity_description.salt_key)
        return self.coordinator.data.get(self._key)

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        if self.entity_description.salt_key is None:
            return self.native_value is not None
        return self.coordinator.salt_tracker.is_configured and self.native_value is not None
