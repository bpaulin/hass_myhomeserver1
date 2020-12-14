"""Myhomeserver1 home assistant light integration."""
import logging

from brownpaperbag.bpbgate import BpbGate
from homeassistant.components.light import LightEntity
from homeassistant.const import CONF_EVENT
from homeassistant.helpers.restore_state import RestoreEntity

from . import DOMAIN

WHO_LIGHT = "1"

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    # pylint: disable=unused-argument
    """Setup the BrownPaperBage Light platform."""
    gate_data = hass.data[DOMAIN]
    gate = gate_data["gate"]

    gate_light_ids = await gate.get_light_ids()

    if config.get(CONF_EVENT):
        hass.data[DOMAIN][WHO_LIGHT] = {}
        hass_lights = [
            BrownPaperBagPushLight(light, gate) for light in gate_light_ids.keys()
        ]
        for hass_light in hass_lights:
            hass.data[DOMAIN][WHO_LIGHT][hass_light.light_id] = hass_light
    else:
        hass_lights = [
            BrownPaperBagLight(light, gate) for light in gate_light_ids.keys()
        ]
    async_add_entities(hass_lights)
    return True


class BrownPaperBagLight(LightEntity, RestoreEntity):
    """Representation of an BrownPaperBag Light."""

    def __init__(self, light_address, gate: BpbGate):
        """Initialize an BrownPaperBageLight."""
        self._gate = gate
        self._light_id = light_address
        self._state = None

    @property
    def light_id(self):
        """Myhomeserver1 light id."""
        return self._light_id

    @property
    def should_poll(self) -> bool:
        return True

    @property
    def name(self):
        """Return the display name of this light."""
        return "myhomeserver1_" + self._light_id

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the light on."""
        self._state = await self._gate.turn_on_light(self._light_id)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the light off."""
        self._state = await self._gate.turn_off_light(self._light_id)

    async def async_update(self):
        """Get state from myhomeserver1."""
        self._state = await self._gate.is_light_on(self._light_id)

    async def async_added_to_hass(self):
        """Call when entity about to be added to hass."""
        # If not None, we got an initial value.
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if not state:
            return
        self._state = state.state == "on"


class BrownPaperBagPushLight(BrownPaperBagLight):
    """Representation of an BrownPaperBag Light (local pushing)."""

    async def receive_gate_state(self, bpb_state):
        """Callback to receive state from myhomeserver1."""
        self._state = bpb_state == "1"
        await self.async_update_ha_state()

    @property
    def should_poll(self) -> bool:
        return False
