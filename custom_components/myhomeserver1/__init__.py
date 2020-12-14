"""Myhomeserver1 home assistant integration."""
import asyncio
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from brownpaperbag import BpbCommandSession, BpbEventSession
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT

_LOGGER = logging.getLogger(__name__)

DOMAIN = "myhomeserver1"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_PORT, default=20000): cv.positive_int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_listen_events(hass, config):
    """Listen to myhomserver1 events."""
    gate = BpbEventSession(
        config[DOMAIN].get(CONF_HOST),
        config[DOMAIN].get(CONF_PORT),
        config[DOMAIN].get(CONF_PASSWORD),
    )
    # gate.logger = logging.getLogger(__name__ + ".event")
    await gate.connect()
    while True:
        (who, what, where) = await gate.readevent_exploded()
        try:
            await hass.data[DOMAIN][who][where].receive_gate_state(what)
        except KeyError:
            continue


async def async_setup(hass, config):
    """Set up component."""
    gate = BpbCommandSession(
        config[DOMAIN].get(CONF_HOST),
        config[DOMAIN].get(CONF_PORT),
        config[DOMAIN].get(CONF_PASSWORD),
    )
    hass.data[DOMAIN] = {"gate": gate}
    gate.logger = _LOGGER
    await gate.connect()
    hass.loop.create_task(async_listen_events(hass, config))
    return True
