"""Base entity for JUDO Cloud."""

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import JudoCloudCoordinator


class JudoCloudEntity(CoordinatorEntity[JudoCloudCoordinator]):
    """Base entity tied to one device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: JudoCloudCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        serial = coordinator.data.get("serial_number", coordinator.entry.entry_id)
        self._attr_unique_id = f"{serial}_{key}"
        self._attr_device_info = {
            "identifiers": {("judo_cloud", serial)},
            "manufacturer": "JUDO",
            "model": "SOFTwell S",
            "name": "JUDO SOFTwell S",
            "sw_version": coordinator.data.get("software_version"),
            "hw_version": coordinator.data.get("hardware_version"),
        }
