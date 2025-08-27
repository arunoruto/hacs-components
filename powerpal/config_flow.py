import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import DOMAIN

class PowerPalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Power Pal."""

    VERSION = 1
    config_data = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            user_input["name"] = user_input["name"].strip()
            
            await self.async_set_unique_id(user_input["name"])
            self._abort_if_unique_id_configured()
            
            self.config_data = user_input
            
            if user_input["price_type"] == "static":
                return await self.async_step_static()
            return await self.async_step_dynamic()

        data_schema = vol.Schema({
            vol.Required("name"): str,
            vol.Required("price_type"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["static", "dynamic"],
                    translation_key="price_type",
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
        })
        return self.async_show_form(step_id="user", data_schema=data_schema)

    async def async_step_static(self, user_input=None):
        """Handle the static price configuration step."""
        if user_input is not None:
            name = self.config_data['name']
            entity_object_id = f"{name.lower().replace(' ', '_')}_price"
            
            # Prepare the data dictionary
            user_input["price_entity"] = f"number.{entity_object_id}"
            user_input["initial_price"] = user_input["price"]
            
            self.config_data.update(user_input)
            
            # The only job is to create the entry with the collected data.
            return self.async_create_entry(title=name, data=self.config_data)

        data_schema = vol.Schema({
            vol.Required("price"): vol.Coerce(float),
            vol.Required("source_sensor"): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor"),
            ),
        })
        return self.async_show_form(step_id="static", data_schema=data_schema)

    async def async_step_dynamic(self, user_input=None):
        """Handle the dynamic price configuration step."""
        if user_input is not None:
            self.config_data.update(user_input)
            return self.async_create_entry(title=self.config_data["name"], data=self.config_data)

        data_schema = vol.Schema({
            vol.Required("price_entity"): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor", "input_number", "number"]),
            ),
            vol.Required("source_sensor"): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor"),
            ),
        })
        return self.async_show_form(step_id="dynamic", data_schema=data_schema)