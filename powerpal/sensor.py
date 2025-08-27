import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_utc_time_change
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Power Pal sensor from a config entry."""
    # Pass both hass and the config_entry to the constructor
    async_add_entities([HourlyCostSensor(hass, config_entry)])


class HourlyCostSensor(SensorEntity):
    """A sensor that calculates hourly cost based on a provided price entity."""
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        """Initialize the sensor."""
        config_data = config_entry.data
        # Store the hass object from the constructor
        self._hass = hass
        self._name = config_data["name"]
        self._source_sensor = config_data["source_sensor"]
        self._price_entity = config_data.get("price_entity")

        self._state = None
        self._attr_unique_id = f"{DOMAIN}_{self._name.lower().replace(' ', '_')}"
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._name)},
        )
        self._last_energy_reading = None
    
    # ... The rest of the class is now correct ...
    async def async_added_to_hass(self):
        """Register callbacks when entity is added."""
        self.async_on_remove(
            async_track_utc_time_change(
                self._hass, self.async_calculate_hourly_cost, hour='*', minute=59, second=59
            )
        )
    
    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return f"{self._hass.config.currency}"

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return "mdi:cash-clock"

    async def async_calculate_hourly_cost(self, now):
        """Calculate the cost for the last hour."""
        price_state: State = self._hass.states.get(self._price_entity)
        if price_state is None or price_state.state in ("unknown", "unavailable"):
            _LOGGER.warning("Price entity %s is unavailable.", self._price_entity)
            return
        try:
            price_for_hour = float(price_state.state)
        except (ValueError, TypeError):
            _LOGGER.warning("Could not parse price from %s.", self._price_entity)
            return

        current_state: State = self._hass.states.get(self._source_sensor)
        if current_state is None or current_state.state in ("unknown", "unavailable"):
            _LOGGER.warning("Source sensor %s is unavailable.", self._source_sensor)
            return
        
        try:
            current_energy = float(current_state.state)
        except (ValueError, TypeError):
            _LOGGER.warning("Could not parse state from %s", self._source_sensor)
            return

        if self._last_energy_reading is None:
            _LOGGER.info("First run for '%s'; initializing energy reading to %s kWh", self.name, current_energy)
            self._last_energy_reading = current_energy
            return

        energy_this_hour = 0.0
        if current_energy < self._last_energy_reading:
            _LOGGER.warning("Energy meter for '%s' appears to have reset.", self.name)
            energy_this_hour = current_energy
        else:
            energy_this_hour = current_energy - self._last_energy_reading

        cost_this_hour = energy_this_hour * price_for_hour
        
        self._state = cost_this_hour
        self._last_energy_reading = current_energy
        self.async_write_ha_state()