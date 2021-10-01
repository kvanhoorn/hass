"""
Support for feedparser reading

For more details about this platform, please refer to the documentation at
https://github.com/kvanhoorn/hass
"""

import logging
import voluptuous as vol
from datetime import timedelta
from dateutil import parser
from time import strftime
from subprocess import check_output
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.components.switch import (PLATFORM_SCHEMA)
from homeassistant.components.sensor import SensorEntity

__version__ = '0.1.0'
_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['feedparser']

CONF_NAME = 'name'
CONF_TITLE_ATTR = 'title_attritube'
CONF_URL = 'url'
CONF_ATTRIBUTES = 'attributes'
DOMAIN = 'feedparser'

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=30)
ICON = 'mdi:rss'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_URL): cv.string,
    vol.Required(CONF_TITLE_ATTR, default='title'): cv.string,
    vol.Required(CONF_ATTRIBUTES, default=[]): vol.All(cv.ensure_list, [cv.string]),
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    add_devices([FeedParserSensor(hass, config)])

class FeedParserSensor(Entity):
    """Representation of a feedparser latest entry."""
    
    def __init__(self, hass, config):
        """Initialize the sensor."""
        self.hass = hass
        self._name = config[CONF_NAME]
        self._title_attr = config[CONF_TITLE_ATTR]
        self._feed = config[CONF_URL]
        self._attributes = config[CONF_ATTRIBUTES]
        self._state = None
        self.hass.data[self._name] = {}

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        import feedparser
        parsedFeed = feedparser.parse(self._feed)

        self.hass.data[self._name] = {}

        if not parsedFeed :
            return False
        else:
            entry = parsedFeed.entries[0]
            self._state = entry[self._title_attr]

            for attr in self._attributes:
                if (attr in entry.keys()):
                    self.hass.data[self._name][attr] = entry[attr]

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state
    
    @property
    def icon(self):
        return ICON
    

    @property
    def device_state_attributes(self):
        """Return the state attributes"""
        return self.hass.data[self._name]
