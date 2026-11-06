"""Config flow for Heatpump Efficiency integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_CONSUMED_HEATING,
    CONF_CONSUMED_HOT_WATER,
    CONF_NAME,
    CONF_PRODUCED_HEATING,
    CONF_PRODUCED_HOT_WATER,
    DEFAULT_NAME,
    DOMAIN,
)


def _get_sensor_schema(defaults: dict[str, Any], include_name: bool = True) -> vol.Schema:
    """Build the voluptuous schema for config and options flows."""
    entity_selector = selector.EntitySelector(
        selector.EntitySelectorConfig(domain="sensor")
    )

    schema_dict: dict[Any, Any] = {}
    if include_name:
        schema_dict[
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME))
        ] = selector.TextSelector()

    schema_dict.update(
        {
            vol.Required(
                CONF_CONSUMED_HEATING,
                default=defaults.get(CONF_CONSUMED_HEATING, vol.UNDEFINED),
            ): entity_selector,
            vol.Required(
                CONF_PRODUCED_HEATING,
                default=defaults.get(CONF_PRODUCED_HEATING, vol.UNDEFINED),
            ): entity_selector,
            vol.Required(
                CONF_CONSUMED_HOT_WATER,
                default=defaults.get(CONF_CONSUMED_HOT_WATER, vol.UNDEFINED),
            ): entity_selector,
            vol.Required(
                CONF_PRODUCED_HOT_WATER,
                default=defaults.get(CONF_PRODUCED_HOT_WATER, vol.UNDEFINED),
            ): entity_selector,
        }
    )
    return vol.Schema(schema_dict)


class HeatpumpEfficiencyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Heatpump Efficiency."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            title = user_input.get(CONF_NAME, DEFAULT_NAME)
            return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_get_sensor_schema(user_input or {}, include_name=True),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return HeatpumpEfficiencyOptionsFlowHandler(config_entry)


class HeatpumpEfficiencyOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Heatpump Efficiency."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_config = {**self._config_entry.data, **self._config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_get_sensor_schema(current_config, include_name=False),
        )
