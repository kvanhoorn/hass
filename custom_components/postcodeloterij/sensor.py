"""
Support for fetch postcodeloterij winnings.
"""
import os
from logging import getLogger

from datetime import datetime
from datetime import timedelta
import dateutil.relativedelta
import requests

import voluptuous as vol
import homeassistant.util as util
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = getLogger(__name__)
_RESOURCE = 'https://www.postcodeloterij.nl/public/rest/drawresults/winnings/NPL/P_MT_P%s/?query=%s&resultSize=10' # % (201812, 1234AB)

CONF_POSTCODE = 'postcode'

ATTR_PRIZES = 'prizes'
ATTR_PERIOD = 'period'

SCAN_INTERVAL = timedelta(seconds=1800)

DOMAIN = 'postcodeloterij'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_POSTCODE): cv.string,
    }),
}, extra=vol.ALLOW_EXTRA)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """"Set up the Postcodeloterij component."""
    
    sens = PostcodeloterijSensor(config.get(CONF_POSTCODE))
    add_devices([sens], True)

class PostcodeloterijSensor(Entity):
    """The sensor."""
    
    def __init__(self, postcode):
        self._name = 'Postcodeloterij prijs'
        self._state = None
        self._postcode = postcode
        self._icon = 'mdi:trophy'
        self._prizes = None
        self._period = None
        self.update()
    
    @property
    def name(self):
        return self._name
    
    @property
    def state(self):
        return self._state
    
    @property
    def icon(self):
        return self._icon

    @property
    def device_state_attributes(self):
       """Return the state attributes."""
       return {
           ATTR_PRIZES: self._prizes,
           ATTR_PERIOD: self._period,
       }
    
    def update(self):

        _LOGGER.debug('Fetching data for postcode "%s"', self._postcode)
    
        moment = datetime.today() - dateutil.relativedelta.relativedelta(months=1)
        if (moment.day < 8):
            moment = moment - dateutil.relativedelta.relativedelta(months=1)
        moment_fmt = moment.strftime('%Y%m')
        _LOGGER.debug("Selected moment: %s" , moment_fmt)

        self._url = _RESOURCE % (moment_fmt, self._postcode)
        
        try:
            req = requests.get(
              self._url)
            self.data = req.json()
            _LOGGER.debug(self.data)
            self._state = self.data['prizeCount']
            
            prizes = []
            for p in self.data['wonPrizes']:
                prizes.append(p['description'])
            self._prizes = ', '.join(str(x) for x in prizes)
            self._period = moment.strftime('%m-%Y')
            
        except requests.exceptions.RequestException as ex:
            _LOGGER.error("Error fetching data from %s" % self._url, ex)
            return False
