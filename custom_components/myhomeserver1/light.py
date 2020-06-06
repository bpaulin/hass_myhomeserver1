import logging

import voluptuous as vol

from homeassistant.components.light import Light, PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, CONF_ADDRESS, CONF_DEVICES
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.restore_state import RestoreEntity
from brownpaperbag import BpbGate

DOMAIN = "myhomeserver1"
WHO_LIGHT = "1"

DEPENDENCIES = ["brownpaperbag"]

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_DEVICES): vol.All(
            cv.ensure_list,
            [
                {
                    vol.Required(CONF_NAME): cv.string,
                    vol.Required(CONF_ADDRESS): cv.string,
                }
            ],
        )
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the BrownPaperBage Light platform."""
    gate_data = hass.data[DOMAIN]
    gate = gate_data["gate"]
    hass.data[DOMAIN][WHO_LIGHT] = {}
    hass_lights = [BrownPaperBagLight(light, gate) for light in config[CONF_DEVICES]]
    for hass_light in hass_lights:
        hass.data[DOMAIN][WHO_LIGHT][hass_light.light_id] = hass_light

    async_add_entities(hass_lights)
    return True


class BrownPaperBagLight(Light, RestoreEntity):
    """Representation of an BrownPaperBag Light."""

    def __init__(self, light, gate: BpbGate):
        """Initialize an BrownPaperBageLight."""
        self._gate = gate
        self._light_id = light[CONF_ADDRESS]
        self._name = "myhomeserver1_" + light[CONF_NAME]
        self._state = None

    @property
    def light_id(self):
        return self._light_id

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the zone on."""
        await self._gate.turn_on_light(self._light_id)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the zone on."""
        await self._gate.turn_off_light(self._light_id)

    async def async_update(self):
        self._state = await self._gate.is_light_on(self._light_id)

    async def receive_gate_state(self, bpb_state):
        self._state = bpb_state == "1"
        await self.async_update_ha_state()

    async def async_added_to_hass(self):
        """Call when entity about to be added to hass."""
        # If not None, we got an initial value.
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if not state:
            return
        self._state = state.state == "on"
