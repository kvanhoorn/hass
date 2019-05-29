"""
Support for Cure waste xml reading

For more details about this platform, please refer to the documentation at
https://github.com/kvanhoorn/hass/
"""
import logging
from datetime import (datetime, timedelta)

from custom_components.cure_waste import (DATA_CUREWASTE)
from homeassistant.const import (LENGTH_KILOMETERS, VOLUME_LITERS)
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['cure_waste']

ICON = 'mdi:calendar'
SENSOR_TYPES = {
    'general_waste': ['General waste', '', ICON],
    'biodegradable_waste': ['Biodegradable waste', '', ICON],
    'paper_waste': ['Paper waste', '', ICON],
}

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up a Cure waste sensor."""
    if discovery_info is None:
        return
        
    actual_data = hass.data[DATA_CUREWASTE]
    
    devs = list()
    for t,resource in SENSOR_TYPES.items():
        devs.append(CureWasteSensor(actual_data, t, resource))
        devs.append(CureWasteCountdownSensor(actual_data, t, resource))

    add_devices(devs, True)


class CureWasteSensor(Entity):
    """A CureWaste sensor."""

    def __init__(self, data, t, resource):
        """Initialize sensors from the location."""
        self.data = data.data
        self._name = data.location + ' ' + resource[0]
        self._type = t
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
        value = self.data

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

    def __init__(self, data, t, resource):
        """Initialize sensors from the location."""
        self.data = data.data
        self._name = data.location + ' ' + resource[0] + ' Countdown'
        self._type = t
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
        value = self.data

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
