import logging
import voluptuous as vol
import asyncio

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "myhomeserver1"

REQUIREMENTS = ["brownpaperbag"]

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
    from brownpaperbag import BpbGate, SESSION_EVENT

    gate = BpbGate(
        config[DOMAIN].get(CONF_HOST),
        config[DOMAIN].get(CONF_PORT),
        config[DOMAIN].get(CONF_PASSWORD),
    )
    gate.logger = _LOGGER
    await gate.command_session(SESSION_EVENT)
    while True:
        (who, what, where) = await gate.readevent_exploded()
        try:
            await hass.data[DOMAIN][who][where].receive_gate_state(what)
        except KeyError:
            continue


async def async_setup(hass, config):
    from brownpaperbag import BpbGate

    gate = BpbGate(
        config[DOMAIN].get(CONF_HOST),
        config[DOMAIN].get(CONF_PORT),
        config[DOMAIN].get(CONF_PASSWORD),
    )
    hass.data[DOMAIN] = {"gate": gate}
    gate.logger = _LOGGER
    await gate.command_session()
    hass.loop.create_task(async_listen_events(hass, config))
    return True
