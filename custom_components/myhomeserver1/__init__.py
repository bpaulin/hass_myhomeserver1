"""Myhomeserver1 home assistant integration."""
import asyncio
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from brownpaperbag import BpbCommandSession, BpbEventSession
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_EVENT

_LOGGER = logging.getLogger(__name__)

DOMAIN = "myhomeserver1"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_PORT, default=20000): cv.positive_int,
                vol.Optional(CONF_EVENT, default=False): cv.boolean,
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
    gate.logger = _LOGGER
    await gate.connect()
    await asyncio.sleep(10)
    while True:
        try:
            (who, what, where) = await gate.readevent_exploded()
        except Exception as e:
            _LOGGER.error("fail to read gateway event ")
        try:
            await hass.data[DOMAIN][who][where].receive_gate_state(what)
        except KeyError:
            _LOGGER.debug("wrong event who:%s what:%s where:%s", who, what, where)


async def async_setup(hass, config):
    """Set up component."""
    gate = BpbCommandSession(
        config[DOMAIN].get(CONF_HOST),
        config[DOMAIN].get(CONF_PORT),
        config[DOMAIN].get(CONF_PASSWORD),
    )
    hass.data[DOMAIN] = {"gate": gate, "event": config[DOMAIN].get(CONF_EVENT)}
    gate.logger = _LOGGER
    _LOGGER.warning(config[DOMAIN].get(CONF_EVENT))
    await gate.connect()
    if config[DOMAIN].get(CONF_EVENT):
        hass.loop.create_task(async_listen_events(hass, config))
    return True
