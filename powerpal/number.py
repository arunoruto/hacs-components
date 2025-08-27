"""Number platform for Power Pal."""
from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number platform."""
    if "initial_price" not in config_entry.data:
        return
        
    name = config_entry.data["name"]
    entity_object_id = f"{name.lower().replace(' ', '_')}_price"
    
    # Pass both hass and the config_entry to the constructor
    async_add_entities([PowerPalNumber(hass, config_entry, entity_object_id)])


class PowerPalNumber(NumberEntity):
    """Representation of a Power Pal number entity."""
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, object_id: str) -> None:
        """Initialize the number entity."""
        name = config_entry.data["name"]
        
        self._attr_unique_id = object_id
        self._attr_name = f"{name} Price"
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, name)},
        )

        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 0.001
        self._attr_native_value = config_entry.data["initial_price"]
        # Use the hass object from the constructor to get the currency
        self._attr_native_unit_of_measurement = f"{hass.config.currency}/kWh"

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._attr_native_value = value
        self.async_write_ha_state()