
"""
Support for Cure Waste collection days.
"""
import logging
import socket
import requests
import asyncio
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (CONF_SCAN_INTERVAL)
from homeassistant.helpers import discovery

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = []

CONF_POSTALCODE = 'postalcode'
CONF_HOUSENUMBER = 'housenumber'
CONF_LOCATION = 'location'

DOMAIN = 'cure_waste'
DATA_CUREWASTE = 'cure_waste'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_POSTALCODE): cv.string,
        vol.Required(CONF_HOUSENUMBER): cv.string,
        vol.Optional(CONF_LOCATION, default='Home'): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=270): cv.positive_int,
    })
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up the CureWaste component."""
    conf = config.get(DOMAIN)
    hass.data[DATA_CUREWASTE] = CureWaste(hass, conf)

    _LOGGER.debug("Setup CureWaste")

    discovery.load_platform(hass, 'sensor', DOMAIN, {}, config)

    return True

class CureWaste(object):
    """Structure CureWaste functions for hass."""
    
    def __init__(self, hass, conf):
        """Init CureWaste devices."""
        self._base_url = 'https://afvalkalender.cure-afvalbeheer.nl/rest/adressen/'
        self._postalcode = conf.get(CONF_POSTALCODE)
        self._housenumber = conf.get(CONF_HOUSENUMBER)
        self._location = conf.get(CONF_LOCATION)
        self.getData()

    def getData(self):
        bag_req = None

        _LOGGER.debug("Running update of data retrieval")
        
        try:
            bag_req = requests.get(
              self._base_url + self._postalcode + '-' + str(self._housenumber))
            bag_data = bag_req.json()
            if bag_data == []:
              _LOGGER.error("Your address '%s, %s' is not available for Cure Waste" % 
                (self._postalcode, str(self._housenumber)))
              return False
            self._bag_id = bag_data[0]['bagId']
        except requests.exceptions.RequestException as ex:
            _LOGGER.error("Error fetching data from %s", bag_req.url, ex)
            return False

        try:
            waste_req = requests.get(self._base_url + self._bag_id + '/afvalstromen')
            self.curedata = waste_req.json()
        except requests.exceptions.RequestException as ex:
            _LOGGER.error("Error fetching data from %s", waste_req.url, ex)
            return False
        
        return True
    
    @property
    def data(self):
        return self.curedata
    
    @property
    def location(self):
        return self._location