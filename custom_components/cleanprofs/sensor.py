"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
  SensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from logging import getLogger
from datetime import datetime
from datetime import timedelta
import dateutil.relativedelta
import requests, re
from lxml import html

DOMAIN = 'Cleanprofs'

_LOGGER = getLogger(__name__)
_RESOURCE = 'https://crm.cleanprofs.nl/search/planning' # form post with zipcode and street_number

CONF_POSTALCODE = 'postalcode'
CONF_HOUSENUMBER = 'housenumber'
CONF_INDEX = 'index'

SCAN_INTERVAL = timedelta(seconds=3600)

CONFIG_SCHEMA = vol.Schema({
  DOMAIN: vol.Schema({
    vol.Required(CONF_POSTALCODE): cv.string,
    vol.Required(CONF_HOUSENUMBER): cv.string
  }),
}, extra=vol.ALLOW_EXTRA)

def setup_platform(hass, config, add_devices, discovery_info=None):
  """Set up the Cleanprofs component."""

  _LOGGER.debug('Set up platform Cleanprofs')

  sens = CleanprofsSensor(config.get(CONF_POSTALCODE), config.get(CONF_HOUSENUMBER), 0) # next
  sens2 = CleanprofsSensor(config.get(CONF_POSTALCODE), config.get(CONF_HOUSENUMBER), 1) # next next
  add_devices([sens, sens2], True)

class CleanprofsSensor(SensorEntity):
  """The sensor."""

  def __init__(self, postalcode, housenumber, index):

    _LOGGER.debug('Set up sensor')

    self._name = 'Cleanprofs date %s' % (index + 1)
    self._state = None
    self._index = index
    self._postalcode = postalcode
    self._housenumber = housenumber
    self._icon = 'mdi:spray-bottle'
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
  def extra_state_attributes(self):
    """Return the state attributes."""
    return {
      CONF_POSTALCODE: self._postalcode,
      CONF_HOUSENUMBER: self._housenumber,
      CONF_INDEX: self._index
    }

  def update(self):

    _LOGGER.debug('Fetching data for postcode "%s" and housenumber "%s"', (self._postalcode, self._housenumber))
    
    data = {
      "zipcode": self._postalcode,
      "street_number": str(self._housenumber)
    }

    result = []
    
    # try:
    req = requests.post(
      _RESOURCE,
      data=data)
    #except:
    #  _LOGGER.warning("Failed to get data")

    # try:
    tree = html.fromstring(req.content)
    activities = tree.xpath("//div[@class='nk-tb-item']")
    
    for i, activity in enumerate(activities):

      type = re.search("[A-Z]{3}", str(activity.xpath(".//span[@class='tb-lead']")[0].text_content()))[0]
      day = activity.xpath(".//span[@class='tb-lead ccap']")[0].text.replace("\n", "").strip()
      date = activity.xpath(".//div[@class='nk-tb-col']")[2].text_content().replace("\n", "").strip()
      now = datetime.now()

      parsed_date = datetime.strptime(date, '%d %b').date()
      if parsed_date.month < now.month:
        parsed_date = parsed_date.replace(year=(now.year + 1))
      else:
        parsed_date = parsed_date.replace(year=now.year)

      if i == self._index:
        self._wastetype = type
        self._state = datetime.strftime(parsed_date, "%d-%m-%Y")

    #except:
     # _LOGGER.warning("Failed to parse data")

