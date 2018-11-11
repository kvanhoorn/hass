"""
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/device_tracker.mind/
"""
import logging

from custom_components.mind import DATA_MIND
from homeassistant.components.device_tracker import (
    PLATFORM_SCHEMA, DEFAULT_SCAN_INTERVAL)
from homeassistant.helpers.event import track_point_in_utc_time
from homeassistant import util

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['mind']

def setup_scanner(hass, config, see, discovery_info=None):
    """Set up a Mind tracker."""
    if discovery_info is None:
        return
    
    interval = DEFAULT_SCAN_INTERVAL

    def update(now):
        """Update the car on every interval time."""

        for vehicle in hass.data[DATA_MIND].vehicles():
            attrs = {
                'street': vehicle.street + ' ' + vehicle.number,
                'city': vehicle.city,
                'country': vehicle.country,
            }
            see(dev_id=vehicle.license_plate, host_name=vehicle.brand, gps=(vehicle.lat, vehicle.lon), attributes=attrs, icon='mdi:car')
            
        track_point_in_utc_time(hass, update, util.dt.utcnow() + interval)
        return True

    return update(util.dt.utcnow())