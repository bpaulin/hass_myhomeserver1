"""Myhomeserver1 home assistant cover integration."""
import logging
from datetime import datetime, timedelta

from brownpaperbag.bpbgate import COVER_CLOSING, COVER_OPENING, BpbGate
from homeassistant.components.cover import CoverEntity

from homeassistant.const import CONF_EVENT
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.restore_state import RestoreEntity

from . import DOMAIN

WHO_COVER = "2"

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the BrownPaperBage Cover platform."""
    # pylint: disable=unused-argument
    gate_data = hass.data[DOMAIN]
    gate = gate_data["gate"]

    gate_cover_ids = await gate.get_cover_ids()

    if config.get(CONF_EVENT):
        hass.data[DOMAIN][WHO_COVER] = {}
        hass_covers = [
            BrownPaperBagPushCover(cover, gate) for cover in gate_cover_ids.keys()
        ]
        for hass_cover in hass_covers:
            hass.data[DOMAIN][WHO_COVER][hass_cover.cover_id] = hass_cover
    else:
        hass_covers = [
            BrownPaperBagCover(cover, gate) for cover in gate_cover_ids.keys()
        ]
    async_add_entities(hass_covers)
    return True


class BrownPaperBagCover(CoverEntity, RestoreEntity):
    """Representation of BrownPaperBag cover."""

    def __init__(self, cover_address, gate: BpbGate):
        """Initialize the cover."""
        self._gate = gate
        self._cover_id = cover_address
        self._name = "myhomeserver1_" + cover_address
        self._state = None

    @property
    def cover_id(self):
        """Myhomeserver1 cover id."""
        return self._cover_id

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def name(self):
        """Return the name of the cover."""
        return self._name

    async def async_open_cover(self, **kwargs):
        """Move the cover."""
        self._state = await self._gate.open_cover(self._cover_id)

    async def async_close_cover(self, **kwargs):
        """Move the cover down."""
        self._state = await self._gate.close_cover(self._cover_id)

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        self._state = await self._gate.stop_cover(self._cover_id)

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
        return None

    @property
    def current_cover_position(self):
        return None


class BrownPaperBagPushCover(BrownPaperBagCover):
    """Representation of BrownPaperBag cover (local pushing)."""

    def __init__(self, cover_address, gate: BpbGate):
        """Initialize the cover."""
        super().__init__(cover_address, gate)
        self._course_duration = 25
        self._listener = None
        self._last_received = None
        self._last_position = 99
        self._expect_change = False

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def is_closed(self):
        return self.current_cover_position <= 0

    def _cancel_listener(self):
        if self._listener:
            self._listener()
            self._listener = None

    async def async_open_cover(self, **kwargs):
        """Move the cover."""
        self._expect_change = True
        self._cancel_listener()
        self._state = await super().async_open_cover()

    async def async_close_cover(self, **kwargs):
        """Move the cover down."""
        self._expect_change = True
        self._cancel_listener()
        self._state = await super().async_close_cover()

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        self._expect_change = True
        self._cancel_listener()
        self._state = await super().async_stop_cover()

    async def receive_gate_state(self, bpb_state):
        """Callback to receive state from myhomeserver1."""
        this_call = datetime.now()
        if self._last_received is None:
            self._last_received = this_call
        time_delta = (this_call - self._last_received).total_seconds()
        if self.is_closing:
            self._last_position -= time_delta * 100 / self._course_duration
            if self._last_position < 0:
                self._last_position = 0
        if self.is_opening:
            self._last_position += time_delta * 100 / self._course_duration
            if self._last_position > 100:
                self._last_position = 100
        if self._state != bpb_state:
            self._state = bpb_state

        self._last_received = this_call
        await self.async_update_ha_state()

    @property
    def current_cover_position(self):
        return self._last_position

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        position = kwargs["position"]
        if position < 5:
            return self.close_cover()
        if position > 95:
            return self.open_cover()
        await self.async_stop_cover()

        async def handle_event(event):
            # pylint: disable=unused-argument
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
        state = await self.async_get_last_state()
        if state:
            self._last_position = state.as_dict()["attributes"]["current_position"]
