import logging

import voluptuous as vol

from homeassistant.components.cover import (
    CoverDevice,
    PLATFORM_SCHEMA,
    SUPPORT_OPEN,
    SUPPORT_CLOSE,
    SUPPORT_STOP,
    STATE_OPENING,
    STATE_CLOSING,
)
from homeassistant.const import CONF_NAME, CONF_ADDRESS, CONF_DEVICES
import homeassistant.helpers.config_validation as cv
from datetime import datetime, timedelta
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.restore_state import RestoreEntity
from brownpaperbag.bpbgate import BpbGate, COVER_CLOSING, COVER_OPENING, COVER_STOPPED

DOMAIN = "myhomeserver1"
WHO_COVER = "2"
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
    """Setup the BrownPaperBage Cover platform."""
    gate_data = hass.data[DOMAIN]
    gate = gate_data["gate"]
    hass.data[DOMAIN][WHO_COVER] = {}
    hass_covers = [BrownPaperBagCover(cover, gate) for cover in config[CONF_DEVICES]]
    for hass_cover in hass_covers:
        hass.data[DOMAIN][WHO_COVER][hass_cover.cover_id] = hass_cover

    async_add_entities(hass_covers)
    return True


class BrownPaperBagCover(CoverDevice, RestoreEntity):
    """Representation of BrownPaperBag cover."""

    def __init__(self, cover, gate: BpbGate):
        """Initialize the cover."""
        self._course_duration = 25
        self._gate = gate
        self._cover_id = cover[CONF_ADDRESS]
        self._name = "myhomeserver1_" + cover[CONF_NAME]
        self._state = None
        self._listener = None
        self._last_received = None
        self._last_position = 99
        self._expect_change = False

    @property
    def cover_id(self):
        return self._cover_id

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def name(self):
        """Return the name of the cover."""
        return self._name

    def cancel_listener(self):
        if self._listener:
            self._listener()
            self._listener = None

    async def async_open_cover(self, **kwargs):
        """Move the cover."""
        self._expect_change = True
        self.cancel_listener()
        await self._gate.open_cover(self._cover_id)

    async def async_close_cover(self, **kwargs):
        """Move the cover down."""
        self._expect_change = True
        self.cancel_listener()
        await self._gate.close_cover(self._cover_id)

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        self._expect_change = True
        self.cancel_listener()
        await self._gate.stop_cover(self._cover_id)

    async def async_update(self):
        """Retrieve latest state."""
        self._state = await self._gate.get_cover_state(self._cover_id)

    @property
    def is_closing(self):
        return self._state == COVER_CLOSING

    @property
    def is_opening(self):
        return self._state == COVER_OPENING

    @property
    def is_closed(self):
        return self.current_cover_position <= 0

    async def receive_gate_state(self, bpb_state):
        this_call = datetime.now()
        if self._last_received is None:
            self._last_received = this_call
        td = (this_call - self._last_received).total_seconds()
        if self.is_closing:
            self._last_position -= td * 100 / self._course_duration
            if self._last_position < 0:
                self._last_position = 0
        if self.is_opening:
            self._last_position += td * 100 / self._course_duration
            if self._last_position > 100:
                self._last_position = 100
        if self._state != bpb_state:
            self._state = bpb_state

        self._last_received = this_call
        await self.async_update_ha_state()

    @property
    def current_cover_position(self):
        return self._last_position

    async def async_set_cover_position(self, position):
        """Move the cover to a specific position."""

        if position < 5:
            return self.close_cover()
        if position > 95:
            return self.open_cover()
        await self.async_stop_cover()

        async def handle_event(event):
            await self.async_stop_cover()

        if position < self._last_position:
            next_msg = datetime.now() + timedelta(
                seconds=(self.current_cover_position - position)
                * self._course_duration
                / 100
            )
            await self.async_close_cover()
        else:
            next_msg = datetime.now() + timedelta(
                seconds=(position - self.current_cover_position)
                * self._course_duration
                / 100
            )
            await self.async_open_cover()
        self._listener = async_track_point_in_time(
            self.platform.hass, handle_event, next_msg
        )

    async def async_added_to_hass(self):
        """Call when entity about to be added to hass."""
        # If not None, we got an initial value.
        await super().async_added_to_hass()
        if self._state is not None:
            return

        state = await self.async_get_last_state()
        if state:
            self._last_position = state.as_dict()["attributes"]["current_position"]
