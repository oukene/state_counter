"""Constants for the Detailed Hello World Push integration."""
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

# This is the internal name of the integration, it should also match the directory
# name for the integration.
DOMAIN = "state_counter"
NAME = "State Counter"
VERSION = "1.0.0"

CONF_DEVICE_NAME = "device_name"
CONF_ORIGIN_ENTITY = "origin_entity"
CONF_COUNT_WAIT_TIME = "count_wait_time"
CONF_CONTINUOUS_TIMER = "continuous_timer"
CONF_ENTITIES = "entities"
CONF_ADD_ANODHER = "add_another"
CONF_NAME = "name"
CONF_MAX_COUNT = "count_max"

CONF_ENTITY_STATE = "entity_state"
CONF_OPERATOR = "operator"
CONF_COUNT_VALUE = "count_value"
CONF_STATE = "state"


NUMBER_MIN = 0
NUMBER_MAX = 10

OPTIONS = [
    (CONF_ORIGIN_ENTITY, "", cv.string),
    (CONF_COUNT_WAIT_TIME, "0.5", vol.All(vol.Coerce(float), vol.Range(0, 1))),
]


EQUAL = "equal"
NOT_EQUAL = "not equal"
BIGGER_THAN = "bigger than"
SMALLER_THAN = "smaller than"


OPERATOR_TYPES = [
    EQUAL,
    NOT_EQUAL,
    BIGGER_THAN,
    SMALLER_THAN
]