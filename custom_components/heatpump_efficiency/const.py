"""Constants for the Heatpump Efficiency integration."""

from typing import Final

DOMAIN: Final = "heatpump_efficiency"

CONF_NAME: Final = "name"
CONF_CONSUMED_HEATING: Final = "consumed_heating_entity"
CONF_PRODUCED_HEATING: Final = "produced_heating_entity"
CONF_CONSUMED_HOT_WATER: Final = "consumed_hot_water_entity"
CONF_PRODUCED_HOT_WATER: Final = "produced_hot_water_entity"

DEFAULT_NAME: Final = "Wärmepumpe Effizienz"

PERIOD_TODAY: Final = "today"
PERIOD_MONTH: Final = "month"
PERIOD_YEAR: Final = "year"
PERIOD_TOTAL: Final = "total"

PERIODS: Final = [
    PERIOD_TODAY,
    PERIOD_MONTH,
    PERIOD_YEAR,
    PERIOD_TOTAL,
]

CATEGORY_HEATING: Final = "heating"
CATEGORY_HOT_WATER: Final = "hot_water"
CATEGORY_TOTAL: Final = "total"

CATEGORIES: Final = [
    CATEGORY_HEATING,
    CATEGORY_HOT_WATER,
    CATEGORY_TOTAL,
]
