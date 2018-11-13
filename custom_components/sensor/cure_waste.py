"""
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.mind/
"""
import os
import logging

from datetime import datetime
from datetime import timedelta

import voluptuous as vol
import requests

from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.util.json import load_json, save_json

REQUIREMENTS = []

_LOGGER = logging.getLogger(__name__)

CONF_POSTALCODE = 'postalcode'
CONF_HOUSENUMBER = 'housenumber'
CONF_LOCATION = 'location'

DEPENDENCIES = ['http']

ICON = 'mdi:calendar'

CUREWASTE_RESOURCE_LIST = {
    'general_waste': ['General waste', '', ICON],
    'biodegradable_waste': ['Biodegradable waste', '', ICON],
    'paper_waste': ['Paper waste', '', ICON],
}

CONFIG_SCHEMA = vol.Schema({
    vol.Required(CONF_POSTALCODE): cv.string,
    vol.Required(CONF_HOUSENUMBER): cv.string,
    vol.Optional(CONF_LOCATION, default='Home'): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up a Cure waste sensor."""
    location = config.get(CONF_LOCATION)
    postalcode = config.get(CONF_POSTALCODE)
    housenumber = config.get(CONF_HOUSENUMBER)
    data = CureWasteData(postalcode, housenumber)

    if not data.update():
      return False

    devs = []
    for t,resource in CUREWASTE_RESOURCE_LIST.items():
        devs.append(CureWasteSensor(data, location, t, resource))
        devs.append(CureWasteCountdownSensor(data, location, t, resource))

    add_devices(devs, True)


class CureWasteSensor(Entity):
    """A CureWaste sensor."""

    def __init__(self, data, location, t, resource):
        """Initialize sensors from the location."""
        self.data = data
        self._name = location + ' ' + resource[0]
        self._type = t
        self._location = location
        self._state = None
        self._unit_of_measurement = resource[1]
        self._icon = resource[2]

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
        value = self.data.data
        
        if self._type == 'general_waste':
            for l in value:
                if l['title'] == 'Restafval' and l['ophaaldatum'] is not None:
                    self._state = l['ophaaldatum']
        if self._type == 'biodegradable_waste':
            for l in value:
                if l['title'] == 'Groente, fruit- en tuinafval' and l['ophaaldatum'] is not None:
                    self._state = l['ophaaldatum']
        if self._type == 'paper_waste':
            for l in value:
                if l['title'] == 'Papier en karton' and l['ophaaldatum'] is not None:
                    self._state = l['ophaaldatum']


class CureWasteCountdownSensor(Entity):
    """A CureWaste sensor."""

    def __init__(self, data, location, t, resource):
        """Initialize sensors from the location."""
        self.data = data
        self._name = location + ' ' + resource[0] + ' Countdown'
        self._type = t
        self._location = location
        self._state = None
        self._unit_of_measurement = resource[1]
        self._icon = resource[2]

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
        value = self.data.data
        
        if self._type == 'general_waste':
            for l in value:
                if l['title'] == 'Restafval' and l['ophaaldatum'] is not None:
                    d = datetime.strptime(l['ophaaldatum'], '%Y-%m-%d') + timedelta(days=1)
                    self._state = (d - datetime.now()).days
        if self._type == 'biodegradable_waste':
            for l in value:
                if l['title'] == 'Groente, fruit- en tuinafval' and l['ophaaldatum'] is not None:
                    d = datetime.strptime(l['ophaaldatum'], '%Y-%m-%d') + timedelta(days=1)
                    self._state = (d - datetime.now()).days
        if self._type == 'paper_waste':
            for l in value:
                if l['title'] == 'Papier en karton' and l['ophaaldatum'] is not None:
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

    def update(self):
        bag_req = None
        
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