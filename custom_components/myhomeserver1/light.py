import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from brownpaperbag.bpbgate import BpbGate
from homeassistant.components.light import PLATFORM_SCHEMA, LightEntity
from homeassistant.const import CONF_ADDRESS, CONF_DEVICES, CONF_NAME, CONF_EVENT
from homeassistant.helpers.restore_state import RestoreEntity
from . import DOMAIN

WHO_LIGHT = "1"

_LOGGER = logging.getLogger(__name__)

# PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
#     {
#         vol.Optional(CONF_DEVICES): vol.All(
#             cv.ensure_list,
#             [
#                 {
#                     vol.Required(CONF_NAME): cv.string,
#                     vol.Required(CONF_ADDRESS): cv.string,
#                 }
#             ],
#         )
#     }
# )


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the BrownPaperBage Light platform."""
    gate_data = hass.data[DOMAIN]
    gate = gate_data["gate"]
    hass.data[DOMAIN][WHO_LIGHT] = {}

    gate_light_ids = await gate.get_light_ids()

    hass_lights = [
        BrownPaperBagLight(light, gate, config.get(CONF_EVENT))
        for light in gate_light_ids.keys()
    ]

    if config.get(CONF_EVENT):
        for hass_light in hass_lights:
            hass.data[DOMAIN][WHO_LIGHT][hass_light.light_id] = hass_light

    async_add_entities(hass_lights)
    return True


class BrownPaperBagLight(LightEntity, RestoreEntity):
    """Representation of an BrownPaperBag Light."""

    def __init__(self, light_address, gate: BpbGate, receiving):
        """Initialize an BrownPaperBageLight."""
        self._gate = gate
        self._light_id = light_address
        self._name = "myhomeserver1_" + light_address
        self._state = None
        self._receiving = receiving

    @property
    def light_id(self):
        return self._light_id

    @property
    def should_poll(self) -> bool:
        return not self._receiving

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
        self._state = await self._gate.turn_on_light(self._light_id)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the zone on."""
        self._state = await self._gate.turn_off_light(self._light_id)

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
