"""
Support for fetch easyenergy tarrifs

Usage:

sensor:
  - platform: easyenergy

"""
import os
from logging import getLogger

from datetime import datetime
from datetime import timedelta
from dateutil import tz
import dateutil.relativedelta
import requests

import voluptuous as vol
import homeassistant.util as util
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import PLATFORM_SCHEMA

_LOGGER = getLogger(__name__)
_RESOURCE_POWER = 'https://mijn.easyenergy.com/nl/api/tariff/getapxtariffs?startTimestamp=%sT22:00:00.000Z&endTimestamp=%sT22:00:00.000Z&grouping=' # % (2021-02-02, 2021-02-03)
_RESOURCE_GAS   = 'https://mijn.easyenergy.com/nl/api/tariff/getlebatariffs?startTimestamp=%sT22:00:00.000Z&endTimestamp=%sT22:00:00.000Z&grouping=' # % (2021-02-02, 2021-02-03)

SCAN_INTERVAL = timedelta(seconds=3600)
DOMAIN = 'easyenergy'
LOCAL_ZONE = 'Europe/Amsterdam'
local_tz = tz.gettz(LOCAL_ZONE)

CONF_TIMEDELTA = 'timedelta'
CONF_GASDECIMALS = 'gas_decimals'
CONF_POWERDECIMALS = 'power_decimals'
DEFAULT_DECIMALS = 3

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_TIMEDELTA, default=0): vol.Coerce(int),
        vol.Optional(CONF_GASDECIMALS, default=DEFAULT_DECIMALS): vol.All(vol.Coerce(int), vol.Range(min=1, max=5)),
        vol.Optional(CONF_POWERDECIMALS, default=DEFAULT_DECIMALS): vol.All(vol.Coerce(int), vol.Range(min=1, max=5)),
    }
)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """"Set up the Easyenergy component."""

    _LOGGER.debug('Set up platform with config')
    _LOGGER.debug(config)

    sensorpostfix = ''
    timedelta = config.get(CONF_TIMEDELTA)
    if timedelta < 0:
        sensorpostfix = '_m' + str(timedelta * -1) + 'd'
    if timedelta > 0:
        sensorpostfix = '_' + str(timedelta) + 'd'

    actual_timedelta = timedelta - 1

    GasSensor = EasyEnergyGasSensor(actual_timedelta, config.get(CONF_GASDECIMALS), sensorpostfix)
    PowerSensor = EasyEnergyPowerSensor(actual_timedelta, config.get(CONF_POWERDECIMALS), sensorpostfix)

    add_devices([
        GasSensor,
        PowerSensor], True)

class EasyEnergyGasSensor(Entity):
    """The sensor."""

    def __init__(self, timedelta, decimals, sensorpostfix):
        _LOGGER.debug('Create gas sensor with decimals "%s"', str(decimals))
        self._name = 'Easyenergy Gas' + sensorpostfix
        self._state = None
        self._attributes = {}
        self._timedelta = timedelta
        self._decimals = decimals
        self._icon = 'mdi:euro'
        self._unit = '€/m³'
        self._tarrif = None
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
    def unit_of_measurement(self):
        return self._unit

    @property
    def extra_state_attributes(self):
       """Return the state attributes."""
       return self._attributes    

    def update(self):

        _LOGGER.debug('Fetching data for gas, timedelta "%s"', str(self._timedelta))

        moment1 = datetime.now() + timedelta(days=self._timedelta)
        moment2 = moment1 + timedelta(days=1)
    
        self._url = _RESOURCE_GAS % (moment1.strftime('%Y-%m-%d'), moment2.strftime('%Y-%m-%d'))
        
        try:
            req = requests.get(
              self._url)
            self.data = req.json()
            _LOGGER.debug(self.data)

            averageAmount = 0
            self._attributes['date'] = moment2.strftime('%Y-%m-%d')

            if "Message" in self.data:
                _LOGGER.warning('Received error from easyenergy API "%s"', str(self.data['Message']))

            else:

                for tariff in self.data:
                    _LOGGER.debug("Handle tariff")
                    _LOGGER.debug(tariff)
                    tariffTime = datetime.strptime(tariff['Timestamp'], "%Y-%m-%dT%H:%M:%S%z").astimezone(local_tz).strftime('%H')
                    tariffTitle = "hour%s" % str(tariffTime)
                    tariffAmount = round(tariff['TariffUsage'], self._decimals)
                    self._attributes[tariffTitle] = tariffAmount
                    averageAmount += tariff['TariffUsage']

                averageAmount = averageAmount / len(self.data)
                self._state = round(averageAmount, self._decimals)
            
        except requests.exceptions.RequestException as ex:
            _LOGGER.error("Error fetching data from %s" % self._url, ex)
            return False


class EasyEnergyPowerSensor(Entity):
    """The sensor."""

    def __init__(self, timedelta, decimals, sensorpostfix):
        _LOGGER.debug('Create power sensor with decimals "%s"', str(decimals))
        self._name = 'Easyenergy Power' + sensorpostfix
        self._state = None
        self._attributes = {}
        self._timedelta = timedelta
        self._decimals = decimals
        self._icon = 'mdi:euro'
        self._unit = '€/kWh'
        self._tarrif = None
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
    def unit_of_measurement(self):
        return self._unit

    @property
    def extra_state_attributes(self):
       """Return the state attributes."""
       return self._attributes    

    def update(self):

        _LOGGER.debug('Fetching data for power, timedelta "%s"', str(self._timedelta))

        moment1 = datetime.now() + timedelta(days=self._timedelta)
        moment2 = moment1 + timedelta(days=1)
    
        self._url = _RESOURCE_POWER % (moment1.strftime('%Y-%m-%d'), moment2.strftime('%Y-%m-%d'))
        
        try:
            req = requests.get(
              self._url)
            self.data = req.json()
            _LOGGER.debug(self.data)

            averageAmount = 0
            self._attributes['date'] = moment2.strftime('%Y-%m-%d')

            if "Message" in self.data:
                _LOGGER.warning('Received error from easyenergy API "%s"', str(self.data['Message']))

            else:

                for tariff in self.data:
                    _LOGGER.debug("Handle tariff")
                    _LOGGER.debug(tariff)
                    tariffTime = datetime.strptime(tariff['Timestamp'], "%Y-%m-%dT%H:%M:%S%z").astimezone(local_tz).strftime('%H')
                    tariffTitle = "hour%s" % str(tariffTime)
                    tariffAmount = round(tariff['TariffUsage'], self._decimals)
                    self._attributes[tariffTitle] = tariffAmount
                    averageAmount += tariff['TariffUsage']

                averageAmount = averageAmount / len(self.data)
                self._state = round(averageAmount, self._decimals)
            
        except requests.exceptions.RequestException as ex:
            _LOGGER.error("Error fetching data from %s" % self._url, ex)
            return False
