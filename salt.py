"""Persistent salt-consumption estimates based on softened water volume."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    DEFAULT_SALT_USE_KG_PER_M3,
    DOMAIN,
    SALT_PER_REGENERATION_KG,
    SALT_TANK_CAPACITY_KG,
)

STORAGE_VERSION = 1


@dataclass(slots=True)
class SaltEstimate:
    """Calculated values derived from one manually established salt baseline."""

    consumed_kg: float | None = None
    remaining_kg: float | None = None
    level_percent: float | None = None
    range_days: float | None = None
    regenerations_remaining: int | None = None


class JudoSaltTracker:
    """Store a salt baseline and calculate estimates from softened water."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.salt.{entry_id}"
        )
        self.reference_amount_kg: float | None = None
        self.reference_soft_water_l: int | None = None
        self.reference_at: datetime | None = None
        self.use_kg_per_m3 = DEFAULT_SALT_USE_KG_PER_M3

    @property
    def is_configured(self) -> bool:
        return (
            self.reference_amount_kg is not None
            and self.reference_soft_water_l is not None
            and self.reference_at is not None
        )

    async def async_load(self) -> None:
        data = await self._store.async_load()
        if not isinstance(data, dict):
            return
        try:
            amount = data.get("reference_amount_kg")
            water = data.get("reference_soft_water_l")
            reference_at = data.get("reference_at")
            if amount is not None and water is not None and reference_at:
                self.reference_amount_kg = float(amount)
                self.reference_soft_water_l = int(water)
                self.reference_at = datetime.fromisoformat(str(reference_at))
            self.use_kg_per_m3 = float(
                data.get("use_kg_per_m3", DEFAULT_SALT_USE_KG_PER_M3)
            )
        except (TypeError, ValueError):
            self.reference_amount_kg = None
            self.reference_soft_water_l = None
            self.reference_at = None
            self.use_kg_per_m3 = DEFAULT_SALT_USE_KG_PER_M3

    async def async_set_reference(self, amount_kg: float, soft_water_l: int) -> None:
        self.reference_amount_kg = amount_kg
        self.reference_soft_water_l = soft_water_l
        self.reference_at = datetime.now(timezone.utc)
        await self._async_save()

    async def async_set_use_rate(self, value: float) -> None:
        self.use_kg_per_m3 = value
        await self._async_save()

    async def _async_save(self) -> None:
        await self._store.async_save(
            {
                "reference_amount_kg": self.reference_amount_kg,
                "reference_soft_water_l": self.reference_soft_water_l,
                "reference_at": (
                    self.reference_at.isoformat() if self.reference_at is not None else None
                ),
                "use_kg_per_m3": self.use_kg_per_m3,
            }
        )

    def estimate(self, soft_water_l: int | None) -> SaltEstimate:
        if not self.is_configured or soft_water_l is None:
            return SaltEstimate()

        delta_l = max(0, int(soft_water_l) - int(self.reference_soft_water_l))
        consumed_kg = delta_l / 1000 * self.use_kg_per_m3
        remaining_kg = max(0.0, float(self.reference_amount_kg) - consumed_kg)
        level_percent = min(100.0, remaining_kg / SALT_TANK_CAPACITY_KG * 100)
        regenerations = int(remaining_kg / SALT_PER_REGENERATION_KG)

        elapsed_days = max(
            0.0,
            (datetime.now(timezone.utc) - self.reference_at).total_seconds() / 86400,
        )
        range_days = None
        if elapsed_days >= 1 and consumed_kg >= 0.05:
            range_days = remaining_kg / (consumed_kg / elapsed_days)

        return SaltEstimate(
            consumed_kg=round(consumed_kg, 3),
            remaining_kg=round(remaining_kg, 2),
            level_percent=round(level_percent),
            range_days=round(range_days) if range_days is not None else None,
            regenerations_remaining=regenerations,
        )
