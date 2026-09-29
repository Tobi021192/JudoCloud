"""Binary sensors for JUDO Cloud."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription

from .const import DOMAIN
from .entity import JudoCloudEntity

DESCRIPTION = BinarySensorEntityDescription(
    key="online", name="Gerätestatus", device_class=BinarySensorDeviceClass.CONNECTIVITY
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([JudoCloudOnlineSensor(coordinator)])


class JudoCloudOnlineSensor(JudoCloudEntity, BinarySensorEntity):
    """Cloud-reported device connectivity."""

    entity_description = DESCRIPTION

    def __init__(self, coordinator):
        super().__init__(coordinator, DESCRIPTION.key)

    @property
    def is_on(self):
        return bool(self.coordinator.data.get("online"))
