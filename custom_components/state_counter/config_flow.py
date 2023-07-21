"""Config flow for Hello World integration."""
import logging
import voluptuous as vol
from typing import Any, Dict, Optional
from datetime import datetime

import homeassistant.helpers.config_validation as cv

import homeassistant.helpers.entity_registry

from homeassistant.helpers.device_registry import (
    async_get,
    async_entries_for_config_entry
)

from .const import *
from homeassistant.helpers import selector
from homeassistant import config_entries, exceptions
from homeassistant.core import callback
from homeassistant.config import CONF_NAME


_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hello World."""

    VERSION = 1
    # Pick one of the available connection classes in homeassistant/config_entries.py
    # This tells HA if it should be asking for updates, or it'll be notified of updates
    # automatically. This example uses PUSH, as the dummy hub will notify HA of
    # changes.
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle the initial step."""
        # This goes through the steps to take the user through the setup process.
        # Using this it is possible to update the UI and prompt for additional
        # information. This example provides a single form (built from `DATA_SCHEMA`),
        # and when that has some validated input, it calls `async_create_entry` to
        # actually create the HA config entry. Note the "title" value is returned by
        # `validate_input` above.
        errors = {}
        if user_input is not None:
            # if user_input[CONF_NETWORK_SEARCH] == True:
            #    return self.async_create_entry(title=user_input[CONF_AREA_NAME], data=user_input)
            # else:
            self.data = user_input
            #self.data[CONF_SWITCHES] = []
            # self.devices = await get_available_device()
            # return await self.async_step_hosts()
            return self.async_create_entry(title=user_input[CONF_DEVICE_NAME], data=self.data)

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_NAME): cv.string
                }), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Handle a option flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry
        self.data = {}
        if CONF_ENTITIES in config_entry.options:
            self.data[CONF_ENTITIES] = config_entry.options[CONF_ENTITIES]
        else:
            _LOGGER.debug("set entity dict")
            self.data[CONF_ENTITIES] = {}

    async def async_step_init(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:

        errors: Dict[str, str] = {}
        
        all_entities = {}
        all_entities_by_id = {}

        entity_registry = homeassistant.helpers.entity_registry.async_get(
            self.hass)
        entities = homeassistant.helpers.entity_registry.async_entries_for_config_entry(
            entity_registry, self.config_entry.entry_id)

        device_registry = async_get(self.hass)
        devices = async_entries_for_config_entry(
            device_registry, self.config_entry.entry_id)

        # Default value for our multi-select.
        _LOGGER.debug("entities : %s", self.data[CONF_ENTITIES])
        for key in self.data[CONF_ENTITIES]:
            host = self.data[CONF_ENTITIES][key]
            for e in entities:
                if e.original_name == host[CONF_NAME]:
                    name = e.name
                    if name is None:
                        name = e.original_name

                    all_entities[e.entity_id] = '{} - {}'.format(
                        name, host[CONF_ORIGIN_ENTITY])

                    all_entities_by_id[(
                        host[CONF_ORIGIN_ENTITY],
                        host[CONF_NAME],
                        host[CONF_WAIT_TIME],
                        host[CONF_MAX_COUNT],
                    )] = {  
                            "entity_id" : e.entity_id,
                            "state" : host[CONF_STATE]
                         }

        if user_input is not None:
            if not errors:
                self.data[CONF_ENTITIES].clear()
                remove_entities = []
                _LOGGER.debug("input : %s", user_input[CONF_ENTITIES])
                for key in all_entities_by_id:
                    if all_entities_by_id[key]["entity_id"] not in user_input[CONF_ENTITIES]:
                        _LOGGER.debug("remove entity : %s",
                                      all_entities_by_id[key]["entity_id"])
                        remove_entities.append(all_entities_by_id[key]["entity_id"])
                        #self.config_entry.data[CONF_DEVICES].remove( { host[CONF_HOST], [e.name for e in devices if e.id == all_devices_by_host[host[CONF_HOST]]] })
                    else:
                        _LOGGER.debug("append entity : %s", key[0])
                        self.data[CONF_ENTITIES][key[0]] = {
                                CONF_ORIGIN_ENTITY: key[0],
                                CONF_NAME: key[1],
                                CONF_WAIT_TIME: key[2],
                                CONF_MAX_COUNT: key[3],
                                CONF_STATE: all_entities_by_id[key]["state"]
                            }

                for id in remove_entities:
                    entity_registry.async_remove(id)

                if user_input.get(CONF_ADD_ANODHER, False):
                    # if len(self.devices) <= 0:
                    #    return self.async_create_entry(title=self.cnfig_entry.data[CONF_AREA_NAME], data=self.config_entry.data)
                    # else:
                    return await self.async_step_entity()

                if len(self.data[CONF_ENTITIES]) <= 0:
                    for d in devices:
                        device_registry.async_remove_device(d.id)

                # User is done adding repos, create the config entry.
                self.data["modifydatetime"] = datetime.now()
                return self.async_create_entry(title=NAME, data=self.data)

        options_schema = vol.Schema(
            {
                vol.Optional(CONF_ENTITIES, default=list(all_entities)): cv.multi_select(all_entities),
                vol.Optional(CONF_ADD_ANODHER): cv.boolean,

                #vol.Optional(CONF_USE_SETUP_MODE, False, cv.boolean),
                #vol.Optional(CONF_ADD_GROUP_DEVICE, False, cv.boolean),
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=options_schema, errors=errors
        )

    async def async_step_entity(self, user_input: Optional[Dict[str, Any]] = None):
        """Second step in config flow to add a repo to watch."""
        errors: Dict[str, str] = {}
        if user_input is not None:

            if not errors:
                # Input is valid, set data.
                _LOGGER.debug("entity name : %s", user_input[CONF_ORIGIN_ENTITY])
                self.data[CONF_ENTITIES][user_input[CONF_ORIGIN_ENTITY]] = {
                        CONF_ORIGIN_ENTITY: user_input[CONF_ORIGIN_ENTITY],
                        CONF_NAME: user_input.get(CONF_NAME, user_input[CONF_ORIGIN_ENTITY]),
                        CONF_WAIT_TIME: user_input[CONF_WAIT_TIME],
                        CONF_MAX_COUNT: user_input[CONF_MAX_COUNT],
                        CONF_STATE: {},
                    }

                # If user ticked the box show this form again so they can add an
                # additional repo.
                #if user_input.get(CONF_ADD_ANODHER, False):
                    # self.devices.remove(user_input[CONF_SWITCH_ENTITY])
                    # if len(self.devices) <= 0:
                    #    return self.async_create_entry(title=NAME, data=self.data)
                    # else:
                self._current_entity = user_input[CONF_ORIGIN_ENTITY]
                return await self.async_step_state()
                # User is done adding repos, create the config entry.
                #_LOGGER.debug("call async_create_entry")
                #self.data["modifydatetime"] = datetime.now()
                #return self.async_create_entry(title=NAME, data=self.data)

        return self.async_show_form(
            step_id="entity",
            data_schema=vol.Schema(
                    {
                        vol.Required(CONF_ORIGIN_ENTITY, default=None): cv.string,
                        vol.Required(CONF_NAME): cv.string,
                        vol.Required(CONF_WAIT_TIME, default=1000): int,
                        vol.Required(CONF_MAX_COUNT, default=NUMBER_MAX): int,
                        #vol.Optional(CONF_ADD_ANODHER): cv.boolean,
                    }
            ), errors=errors
        )

    async def async_step_state(self, user_input: Optional[Dict[str, Any]] = None):
        """Second step in config flow to add a repo to watch."""
        errors: Dict[str, str] = {}
        if user_input is not None:

            if not errors:
                # Input is valid, set data.
                self.data[CONF_ENTITIES][self._current_entity][CONF_STATE][user_input[CONF_ENTITY_STATE]] = {
                        CONF_OPERATOR: user_input[CONF_OPERATOR],
                        CONF_ENTITY_STATE: user_input[CONF_ENTITY_STATE],
                        CONF_COUNT_VALUE: user_input[CONF_COUNT_VALUE],
                    }

                # If user ticked the box show this form again so they can add an
                # additional repo.
                if user_input.get(CONF_ADD_ANODHER, False):
                    # self.devices.remove(user_input[CONF_SWITCH_ENTITY])
                    # if len(self.devices) <= 0:
                    #    return self.async_create_entry(title=NAME, data=self.data)
                    # else:
                    return await self.async_step_state()
                # User is done adding repos, create the config entry.
                _LOGGER.debug("call async_create_entry")
                self.data["modifydatetime"] = datetime.now()
                return self.async_create_entry(title=NAME, data=self.data)

        return self.async_show_form(
            step_id="state",
            data_schema=vol.Schema(
                    {
                        vol.Required(CONF_OPERATOR, default=EQUAL): selector.SelectSelector(
                            selector.SelectSelectorConfig(options=OPERATOR_TYPES, mode=selector.SelectSelectorMode.DROPDOWN)),
                        vol.Required(CONF_ENTITY_STATE, default=None): cv.string,
                        vol.Required(CONF_COUNT_VALUE, default=1): int,
                        vol.Optional(CONF_ADD_ANODHER): cv.boolean,
                    }
            ), errors=errors
        )

class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
