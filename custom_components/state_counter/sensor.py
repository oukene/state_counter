"""Platform for sensor integration."""
# This file shows the setup for the sensors associated with the cover.
# They are setup in the same way with the call to the async_setup_entry function
# via HA from the module __init__. Each sensor has a device_class, this tells HA how
# to display it in the UI (for know types). The unit_of_measurement property tells HA
# what the unit is, so it can display the correct range. For predefined types (such as
# battery), the unit_of_measurement should match what's expected.
import logging
from threading import Timer
from homeassistant.const import (
    STATE_UNKNOWN, STATE_UNAVAILABLE,
)

import asyncio
from .const import *
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.event import async_track_state_change
from homeassistant.components.sensor import SensorEntity


_LOGGER = logging.getLogger(__name__)

# See cover.py for more details.
# Note how both entities for each roller sensor (battry and illuminance) are added at
# the same time to the same list. This way only a single async_add_devices call is
# required.

ENTITY_ID_FORMAT = DOMAIN + ".{}"

def isNumber(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Add sensors for passed config_entry in HA."""

    hass.data[DOMAIN][config_entry.entry_id]["listener"] = []
        
    device_name = config_entry.data.get(CONF_DEVICE_NAME)
    _LOGGER.debug("data : %s", config_entry.data)
    _LOGGER.debug("options : %s", config_entry.options)
    device = Device(device_name, config_entry)

    new_devices = []

    if config_entry.options.get(CONF_ENTITIES) != None:
        for key in config_entry.options.get(CONF_ENTITIES):
            _LOGGER.debug("key : %s", key)
            entity = config_entry.options[CONF_ENTITIES][key]
            _LOGGER.debug("entity : %s", entity)
            new_devices.append(
                StateCounter(
                    hass,
                    config_entry.entry_id,
                    device,
                    entity[CONF_NAME],
                    entity[CONF_ORIGIN_ENTITY],
                    entity[CONF_COUNT_LATENCY],
                    entity[CONF_CONTINUOUS_TIMER],
                    entity[CONF_MAX_COUNT],
                    entity[CONF_STATE],
                )
            )

        if new_devices:
            async_add_devices(new_devices)

class Device:
    """Dummy roller (device for HA) for Hello World example."""

    def __init__(self, name, config):
        """Init dummy roller."""
        self._id = f"{name}_{config.entry_id}"
        self._name = name
        self._callbacks = set()
        self._loop = asyncio.get_event_loop()
        # Reports if the roller is moving up or down.
        # >0 is up, <0 is down. This very much just for demonstration.

        # Some static information about this device
        self.firmware_version = VERSION
        self.model = name
        self.manufacturer = name

    @property
    def device_id(self):
        """Return ID for roller."""
        return self._id

    @property
    def name(self):
        return self._name

    def register_callback(self, callback):
        """Register callback, called when Roller changes state."""
        self._callbacks.add(callback)

    def remove_callback(self, callback):
        """Remove previously registered callback."""
        self._callbacks.discard(callback)

    # In a real implementation, this library would call it's call backs when it was
    # notified of any state changeds for the relevant device.
    async def publish_updates(self):
        """Schedule call all registered callbacks."""
        for callback in self._callbacks:
            callback()

    def publish_updates(self):
        """Schedule call all registered callbacks."""
        for callback in self._callbacks:
            callback()

# This base class shows the common properties and methods for a sensor as used in this
# example. See each sensor for further details about properties and methods that
# have been overridden.


class SensorBase(SensorEntity):
    """Base representation of a Hello World Sensor."""

    should_poll = False

    def __init__(self, device):
        """Initialize the sensor."""
        self._device = device

    # To link this entity to the cover device, this property must return an
    # identifiers value matching that used in the cover, but no other information such
    # as name. If name is returned, this entity will then also become a device in the
    # HA UI.
    @property
    def device_info(self):
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self._device.device_id)},
            # If desired, the name for the device could be different to the entity
            "name": self._device.name,
            "sw_version": self._device.firmware_version,
            "model": self._device.model,
            "manufacturer": self._device.manufacturer
        }

    # This property is important to let HA know if this entity is online or not.
    # If an entity is offline (return False), the UI will refelect this.
    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return True

    async def async_added_to_hass(self):
        """Run when this Entity has been added to HA."""
        # Sensors should also register callbacks to HA when their state changes
        self._device.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._device.remove_callback(self.async_write_ha_state)


class StateCounter(SensorBase):
    """Representation of a Thermal Comfort Sensor."""

    def __init__(self, hass, entry_id, device, entity_name, origin_entity, count_latency, continuous_timer, max_count, dict_state):
        """Initialize the sensor."""
        super().__init__(device)

        self.hass = hass
        self._origin_entity = origin_entity

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "{}_{}".format(self._device.name, entity_name), hass=hass)
        self._name = "{}".format(entity_name)
        # self._name = "{} {}".format(device.device_id, SENSOR_TYPES[sensor_type][1])
        self._unit_of_measurement = ""
        self._state = None
        self._attributes = {}
        self._attributes[CONF_ORIGIN_ENTITY] = origin_entity
        self._attributes[CONF_COUNT_LATENCY] = count_latency
        self._attributes[CONF_CONTINUOUS_TIMER] = continuous_timer
        self._attributes[CONF_STATE] = dict_state
        self._icon = None
        self._entity_picture = None
        self._reset_timer = None
        self._max_count = max_count
        self._count = NUMBER_MIN
        self._value = NUMBER_MIN

        # self._device_class = SENSOR_TYPES[sensor_type][0]
        self._unique_id = self.entity_id
        self._device = device

        hass.data[DOMAIN][entry_id]["listener"].append(async_track_state_change(
            self.hass, origin_entity, self.switch_entity_listener))
        state = self.hass.states.get(origin_entity)

        #if _is_valid_state(state):
            #self._attributes["switch state"] = state.state
            #self._entity_state = state.state
            #if state.state == "on":
            #    self._force_off = True
            #    self.hass.services.call('homeassistant', 'turn_off', {
            #                            "entity_id": self._origin_entity}, False)

    def check_operator(self, op1, operator, op2):
        _LOGGER.debug("check operator, operator : %s, op1 : %s, op2 : %s", operator, op1, op2)
        if operator == EQUAL:
            return op1 == op2
        elif operator == NOT_EQUAL:
            return op1 != op2
        elif operator == BIGGER_THAN:
            return isNumber(op1) and isNumber(op2) and (float)(op1) > (float)(op2)
        elif operator == SMALLER_THAN:
            return isNumber(op1) and isNumber(op2) and (float)(op1) < (float)(op2)

    def switch_entity_listener(self, entity, old_state, new_state):
        try:
            _LOGGER.debug("call switch_entity_listener, old state : %s, new_state : %s",
                          old_state.state, new_state.state)

            if _is_valid_state(new_state) and old_state.state != new_state.state:
                _LOGGER.debug("operator list : %s, state : %s", self._attributes[CONF_STATE], str(new_state.state))
                for key in self._attributes[CONF_STATE]:
                    ret = False
                    dict_state = self._attributes[CONF_STATE][key]

                    if self.check_operator(new_state.state, dict_state[CONF_OPERATOR], dict_state[CONF_ENTITY_STATE]):
                        self.set_value(int(self._count + dict_state[CONF_COUNT_VALUE]))
                        self.schedule_update_ha_state(True)
        except:
            ''

    def set_value(self, value: float) -> None:
        self._count = int(min(self._max_count, int(value)))
        _LOGGER.debug("call set value : %f", self._count)
        if int(self._count) != NUMBER_MIN:
            if self._attributes[CONF_CONTINUOUS_TIMER] == False:
                if self._reset_timer != None:
                    self._reset_timer.cancel()
                _LOGGER.debug("call timer 1")
                self._reset_timer = Timer(self._attributes[CONF_COUNT_LATENCY]/1000, self.reset)
                self._reset_timer.start()
            else:
                if self._reset_timer == None:
                    self._reset_timer = Timer(self._attributes[CONF_COUNT_LATENCY]/1000, self.reset)
                    _LOGGER.debug("call timer 2")
                    self._reset_timer.start()

    def reset(self) -> None:
        self._value = self._count
        self._device.publish_updates()
        self._count = NUMBER_MIN
        self._value = NUMBER_MIN

        # 여기에 있었지만 위치 바꿈
        self._device.publish_updates()
        self._reset_timer = None

    # def unique_id(self):
    #    """Return Unique ID string."""
    #    return self.unique_id

    """Sensor Properties"""
    @property
    def has_entity_name(self) -> bool:
        return True

    @property
    def unit_of_measurement(self):
        """Return the unit_of_measurement of the device."""
        return self._unit_of_measurement

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return self._attributes

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        # return self._state
        return self._value

    # @property
    # def device_class(self) -> Optional[str]:
    #    """Return the device class of the sensor."""
    #    return self._device_class
    # @property
    # def entity_picture(self):
    #    """Return the entity_picture to use in the frontend, if any."""
    #    return self._entity_picture
    # @property
    # def unit_of_measurement(self):
    #    """Return the unit_of_measurement of the device."""
    #    return self._unit_of_measurement
    # @property
    # def should_poll(self):
    #    """No polling needed."""
    #    return False
    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self._unique_id is not None:
            return self._unique_id

    def update(self):
        """Update the state."""


def _is_valid_state(state) -> bool:
    return state and state.state != STATE_UNKNOWN and state.state != STATE_UNAVAILABLE
