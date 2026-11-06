"""Sensor platform for Heatpump Efficiency integration."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfEnergy,
)
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import (
    CATEGORIES,
    CATEGORY_HEATING,
    CATEGORY_HOT_WATER,
    CATEGORY_TOTAL,
    CONF_CONSUMED_HEATING,
    CONF_CONSUMED_HOT_WATER,
    CONF_NAME,
    CONF_PRODUCED_HEATING,
    CONF_PRODUCED_HOT_WATER,
    DEFAULT_NAME,
    DOMAIN,
    PERIOD_MONTH,
    PERIOD_TODAY,
    PERIOD_TOTAL,
    PERIOD_YEAR,
    PERIODS,
)

_LOGGER = logging.getLogger(__name__)

SOURCE_KEYS = (
    CONF_CONSUMED_HEATING,
    CONF_PRODUCED_HEATING,
    CONF_CONSUMED_HOT_WATER,
    CONF_PRODUCED_HOT_WATER,
)

CATEGORY_ICONS = {
    CATEGORY_HEATING: "mdi:radiator",
    CATEGORY_HOT_WATER: "mdi:water-boiler",
    CATEGORY_TOTAL: "mdi:heat-pump",
}


def _get_period_key(period: str, now: datetime) -> str:
    """Return a string key identifying the current time window for a period."""
    if period == PERIOD_TODAY:
        return now.strftime("%Y-%m-%d")
    if period == PERIOD_MONTH:
        return now.strftime("%Y-%m")
    if period == PERIOD_YEAR:
        return now.strftime("%Y")
    return "total"


def _state_to_kwh(state: State | None) -> float | None:
    """Extract numeric state value and convert to kWh if necessary."""
    if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
        return None
    try:
        value = float(state.state)
    except (ValueError, TypeError):
        return None

    unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
    if unit == UnitOfEnergy.WATT_HOUR:
        return value / 1000.0
    if unit == UnitOfEnergy.MEGA_WATT_HOUR:
        return value * 1000.0
    if unit == UnitOfEnergy.GIGA_WATT_HOUR:
        return value * 1_000_000.0
    return value


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Heatpump Efficiency sensors."""
    config = {**entry.data, **entry.options}

    entities: list[HeatpumpEfficiencySensor] = []
    for period in PERIODS:
        for category in CATEGORIES:
            entities.append(
                HeatpumpEfficiencySensor(
                    hass=hass,
                    entry=entry,
                    config=config,
                    period=period,
                    category=category,
                )
            )

    async_add_entities(entities)


class HeatpumpEfficiencySensor(SensorEntity, RestoreEntity):
    """Representation of a Heatpump Efficiency sensor (COP / JAZ / AZ)."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        config: dict[str, Any],
        period: str,
        category: str,
    ) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry = entry
        self._config = config
        self._period = period
        self._category = category

        translation_key = f"efficiency_{category}_{period}"
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{entry.entry_id}_{translation_key}"
        self._attr_icon = CATEGORY_ICONS.get(category, "mdi:heat-pump")

        device_name = config.get(CONF_NAME, entry.title or DEFAULT_NAME)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=device_name,
            manufacturer="Custom Integration",
            model="Wärmepumpe Effizienz (COP / JAZ)",
            entry_type=DeviceEntryType.SERVICE,
        )

        # Determine which source entities this sensor needs to track
        if category == CATEGORY_HEATING:
            self._relevant_keys = (CONF_CONSUMED_HEATING, CONF_PRODUCED_HEATING)
        elif category == CATEGORY_HOT_WATER:
            self._relevant_keys = (CONF_CONSUMED_HOT_WATER, CONF_PRODUCED_HOT_WATER)
        else:
            self._relevant_keys = SOURCE_KEYS

        self._entity_map: dict[str, str] = {
            key: config[key] for key in self._relevant_keys
        }

        now = dt_util.now()
        self._period_key: str = _get_period_key(self._period, now)

        # Accumulated energy in kWh for the current period (used for today/month/year)
        self._accumulated: dict[str, float] = {
            key: 0.0 for key in self._relevant_keys
        }
        # Last raw reading in kWh from each source sensor
        self._last_reading: dict[str, float | None] = {
            key: None for key in self._relevant_keys
        }

    async def async_added_to_hass(self) -> None:
        """Restore previous state and subscribe to source entity updates."""
        await super().async_added_to_hass()

        now = dt_util.now()
        current_period_key = _get_period_key(self._period, now)
        self._period_key = current_period_key

        # Restore previous period data if available
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.attributes:
            attrs = last_state.attributes
            saved_period_key = attrs.get("period_key")

            if self._period == PERIOD_TOTAL or saved_period_key == current_period_key:
                accumulated_attr = attrs.get("accumulated_kwh", {})
                last_reading_attr = attrs.get("last_reading_kwh", {})
                for key in self._relevant_keys:
                    if isinstance(accumulated_attr, dict) and key in accumulated_attr:
                        try:
                            self._accumulated[key] = float(accumulated_attr[key])
                        except (ValueError, TypeError):
                            pass
                    if isinstance(last_reading_attr, dict) and key in last_reading_attr:
                        val = last_reading_attr[key]
                        if val is not None:
                            try:
                                self._last_reading[key] = float(val)
                            except (ValueError, TypeError):
                                pass

        # Process current states of all source sensors
        for key, entity_id in self._entity_map.items():
            state = self.hass.states.get(entity_id)
            self._process_source_state(key, state)

        # Listen to state changes of the source sensors
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                list(self._entity_map.values()),
                self._async_on_source_state_change,
            )
        )

        # For Today, Month, Year: check period rollover at midnight
        if self._period != PERIOD_TOTAL:
            self.async_on_remove(
                async_track_time_change(
                    self.hass,
                    self._async_check_period_rollover,
                    hour=0,
                    minute=0,
                    second=0,
                )
            )

    def _check_and_handle_rollover(self, now: datetime) -> bool:
        """Reset accumulators if a new day/month/year has started."""
        if self._period == PERIOD_TOTAL:
            return False

        new_period_key = _get_period_key(self._period, now)
        if new_period_key != self._period_key:
            _LOGGER.debug(
                "Period rollover for %s: %s -> %s",
                self.entity_id,
                self._period_key,
                new_period_key,
            )
            self._period_key = new_period_key
            for key, entity_id in self._entity_map.items():
                self._accumulated[key] = 0.0
                current_val = _state_to_kwh(self.hass.states.get(entity_id))
                if current_val is not None:
                    self._last_reading[key] = current_val
            return True
        return False

    def _process_source_state(self, key: str, state: State | None) -> None:
        """Update internal counters from a source entity's state."""
        current_val = _state_to_kwh(state)
        if current_val is None:
            return

        if self._period == PERIOD_TOTAL:
            self._last_reading[key] = current_val
            self._accumulated[key] = current_val
            return

        last_val = self._last_reading[key]
        if last_val is None:
            self._last_reading[key] = current_val
            return

        delta = current_val - last_val
        if delta > 0:
            self._accumulated[key] = round(self._accumulated[key] + delta, 6)
            self._last_reading[key] = current_val
        elif delta < 0:
            # Handle total_increasing meter reset
            self._last_reading[key] = current_val

    @callback
    def _async_on_source_state_change(self, event: Event) -> None:
        """Handle state changes of the monitored energy sensors."""
        self._check_and_handle_rollover(dt_util.now())

        entity_id = event.data.get("entity_id")
        new_state: State | None = event.data.get("new_state")

        for key, mapped_entity_id in self._entity_map.items():
            if mapped_entity_id == entity_id:
                self._process_source_state(key, new_state)

        self.async_write_ha_state()

    @callback
    def _async_check_period_rollover(self, now: datetime) -> None:
        """Handle scheduled midnight check for period rollover."""
        if self._check_and_handle_rollover(now):
            self.async_write_ha_state()

    def _get_consumed_and_produced(self) -> tuple[float, float]:
        """Return (consumed_kwh, produced_kwh) for this sensor's category & period."""
        if self._category == CATEGORY_HEATING:
            consumed = self._accumulated.get(CONF_CONSUMED_HEATING, 0.0)
            produced = self._accumulated.get(CONF_PRODUCED_HEATING, 0.0)
        elif self._category == CATEGORY_HOT_WATER:
            consumed = self._accumulated.get(CONF_CONSUMED_HOT_WATER, 0.0)
            produced = self._accumulated.get(CONF_PRODUCED_HOT_WATER, 0.0)
        else:
            consumed = self._accumulated.get(
                CONF_CONSUMED_HEATING, 0.0
            ) + self._accumulated.get(CONF_CONSUMED_HOT_WATER, 0.0)
            produced = self._accumulated.get(
                CONF_PRODUCED_HEATING, 0.0
            ) + self._accumulated.get(CONF_PRODUCED_HOT_WATER, 0.0)
        return round(consumed, 3), round(produced, 3)

    @property
    def native_value(self) -> float | None:
        """Return the calculated efficiency (COP / AZ / JAZ)."""
        # Wait until all relevant source sensors have reported at least once
        if any(self._last_reading[key] is None for key in self._relevant_keys):
            return None

        consumed, produced = self._get_consumed_and_produced()
        if consumed <= 0:
            return 0.0

        return round(produced / consumed, 2)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes including consumed/produced energy and persistence data."""
        consumed, produced = self._get_consumed_and_produced()
        attrs: dict[str, Any] = {
            "period": self._period,
            "category": self._category,
            "period_key": self._period_key,
            "consumed_kwh": consumed,
            "produced_kwh": produced,
            "accumulated_kwh": dict(self._accumulated),
            "last_reading_kwh": dict(self._last_reading),
        }
        if self._category == CATEGORY_TOTAL:
            attrs["consumed_heating_kwh"] = round(
                self._accumulated.get(CONF_CONSUMED_HEATING, 0.0), 3
            )
            attrs["produced_heating_kwh"] = round(
                self._accumulated.get(CONF_PRODUCED_HEATING, 0.0), 3
            )
            attrs["consumed_hot_water_kwh"] = round(
                self._accumulated.get(CONF_CONSUMED_HOT_WATER, 0.0), 3
            )
            attrs["produced_hot_water_kwh"] = round(
                self._accumulated.get(CONF_PRODUCED_HOT_WATER, 0.0), 3
            )
        return attrs
