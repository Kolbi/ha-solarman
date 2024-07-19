from __future__ import annotations

import logging

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory
from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import *
from .common import *
from .services import *
from .sensor import SolarmanSensor

_LOGGER = logging.getLogger(__name__)

_PLATFORM = get_current_file_name(__name__)


def _create_sensor(coordinator, sensor):
    try:
        entity = SolarmanSwitchEntity(coordinator, sensor)

        entity.update()

        return entity
    except BaseException as e:
        _LOGGER.error(f"Configuring {sensor} failed. [{format_exception(e)}]")
        raise


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    _LOGGER.debug(f"async_setup_entry: {config.options}")
    coordinator = hass.data[DOMAIN][config.entry_id]

    sensors = coordinator.inverter.get_sensors()

    # Add entities.
    #
    _LOGGER.debug("async_setup: async_add_entities")

    async_add_entities(
        _create_sensor(coordinator, sensor)
        for sensor in sensors
        if ("class" in sensor and sensor["class"] == _PLATFORM)
    )
    return True


async def async_unload_entry(hass: HomeAssistant, config: ConfigEntry) -> bool:
    _LOGGER.debug(f"async_unload_entry: {config.options}")
    return True


class SolarmanSwitchEntity(SolarmanSensor, SwitchEntity):
    def __init__(self, coordinator, sensor):
        SolarmanSensor.__init__(self, coordinator, sensor, 0, 0)
        # Set The Device Class of the entity.
        self._attr_device_class = SwitchDeviceClass.SWITCH
        # Set The Category of the entity.
        self._attr_entity_category = EntityCategory.CONFIG

        registers = sensor["registers"]
        registers_length = len(registers)
        if registers_length > 0:
            self.register = sensor["registers"][0]
        if registers_length > 1:
            _LOGGER.warning(
                "SolarmanSwitchEntity.__init__: Contains more than 1 register!"
            )

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        return self._attr_state != 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.coordinator.inverter.service_write_multiple_holding_registers(
            self.register,
            [
                1,
            ],
        )
        self._attr_state = 1
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.coordinator.inverter.service_write_multiple_holding_registers(
            self.register,
            [
                0,
            ],
        )
        self._attr_state = 0
        self.async_write_ha_state()
