"""
Support for Cure waste xml reading

For more details about this platform, please refer to the documentation at
https://github.com/kvanhoorn/hass/
"""
import os
import logging

from datetime import datetime
from datetime import timedelta

import voluptuous as vol
import requests

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.util.json import load_json, save_json

REQUIREMENTS = []

# enable debug logging with:
# logger:
#   logs:
#     custom_components.sensor.cure_waste: debug
_LOGGER = logging.getLogger(__name__)

CONF_POSTALCODE = 'postalcode'
CONF_HOUSENUMBER = 'housenumber'
CONF_LOCATION = 'location'

DEPENDENCIES = ['http']

SCAN_INTERVAL = timedelta(seconds=1800)

ICON = 'mdi:calendar'

CUREWASTE_RESOURCE_LIST = {
    'general_waste': ['General waste', '', ICON],
    'biodegradable_waste': ['Biodegradable waste', '', ICON],
    'paper_waste': ['Paper waste', '', ICON],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_POSTALCODE): cv.string,
    vol.Required(CONF_HOUSENUMBER): cv.string,
    vol.Optional(CONF_LOCATION, default='Home'): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up a Cure waste sensor."""
    location = config.get(CONF_LOCATION)
    postalcode = config.get(CONF_POSTALCODE)
    housenumber = config.get(CONF_HOUSENUMBER)

    devs = []
    for t,resource in CUREWASTE_RESOURCE_LIST.items():
        devs.append(CureWasteSensor(location, postalcode, housenumber, t, resource))
        devs.append(CureWasteCountdownSensor(location, postalcode, housenumber, t, resource))

    add_devices(devs, True)


class CureWasteSensor(Entity):
    """A CureWaste sensor."""

    def __init__(self, location, postalcode, housenumber, t, resource):
        """Initialize sensors from the location."""
        self.data = None
        self._name = location + ' ' + resource[0]
        self._type = t
        self._location = location
        self._postalcode = postalcode
        self._housenumber = housenumber
        self._state = None
        self._unit_of_measurement = resource[1]
        self._icon = resource[2]
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the current state."""
        return self._state

    @property
    def icon(self):
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    def update(self):
        """Retrieve sensor data from the data."""
        self.data = CureWasteData(self._postalcode, self._housenumber)
        value = self.data.data

        _LOGGER.debug("Running update of CureWasteSensor")
        
        if self._type == 'general_waste':
            for l in value:
                if l['icon'] == 'kliko-grijs-rest' and l['ophaaldatum'] is not None:
                    self._state = l['ophaaldatum']
        if self._type == 'biodegradable_waste':
            for l in value:
                if l['icon'] == 'appel-gft' and l['ophaaldatum'] is not None:
                    self._state = l['ophaaldatum']
        if self._type == 'paper_waste':
            for l in value:
                if l['icon'] == 'doos-karton-papier' and l['ophaaldatum'] is not None:
                    self._state = l['ophaaldatum']


class CureWasteCountdownSensor(Entity):
    """A CureWaste sensor."""

    def __init__(self, location, postalcode, housenumber, t, resource):
        """Initialize sensors from the location."""
        self.data = None
        self._name = location + ' ' + resource[0] + ' Countdown'
        self._type = t
        self._location = location
        self._postalcode = postalcode
        self._housenumber = housenumber
        self._state = None
        self._unit_of_measurement = resource[1]
        self._icon = resource[2]
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the current state."""
        return self._state

    @property
    def icon(self):
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    def update(self):
        """Retrieve sensor data from the data."""
        self.data = CureWasteData(self._postalcode, self._housenumber)
        value = self.data.data

        _LOGGER.debug("Running update of CureWasteCountdownSensor")
        
        if self._type == 'general_waste':
            for l in value:
                if l['icon'] == 'kliko-grijs-rest' and l['ophaaldatum'] is not None:
                    d = datetime.strptime(l['ophaaldatum'], '%Y-%m-%d') + timedelta(days=1)
                    self._state = (d - datetime.now()).days
        if self._type == 'biodegradable_waste':
            for l in value:
                if l['icon'] == 'appel-gft' and l['ophaaldatum'] is not None:
                    d = datetime.strptime(l['ophaaldatum'], '%Y-%m-%d') + timedelta(days=1)
                    self._state = (d - datetime.now()).days
        if self._type == 'paper_waste':
            for l in value:
                if l['icon'] == 'doos-karton-papier' and l['ophaaldatum'] is not None:
                    d = datetime.strptime(l['ophaaldatum'], '%Y-%m-%d') + timedelta(days=1)
                    self._state = (d - datetime.now()).days


class CureWasteData(Entity):
    """A CureWaste REST call."""

    def __init__(self, postalcode, housenumber):
        self._base_url = 'https://afvalkalender.cure-afvalbeheer.nl/rest/adressen/'
        self._postalcode = postalcode
        self._housenumber = housenumber
        self._bag_id = None
        self.data = None
        self.update()

    def update(self):
        bag_req = None

        _LOGGER.debug("Running update of data retrieval")
        
        try:
            bag_req = requests.get(
              self._base_url + self._postalcode + '-' + str(self._housenumber))
            bag_data = bag_req.json()
            if bag_data == []:
              _LOGGER.error("Your address '%s, %s' is not available for Cure Waste" % (self._postalcode, str(self._housenumber)))
              return False
            self._bag_id = bag_data[0]['bagId']
        except requests.exceptions.RequestException as ex:
            _LOGGER.error("Error fetching data from %s", bag_req.url, ex)
            return False

        try:
            waste_req = requests.get(self._base_url + self._bag_id + '/afvalstromen')
            self.data = waste_req.json()
        except requests.exceptions.RequestException as ex:
            _LOGGER.error("Error fetching data from %s", waste_req.url, ex)
            return False
        
        return True