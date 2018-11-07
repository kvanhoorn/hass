"""
Pushover platform for notify component.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/notify.pushover/
"""
import logging
import mimetypes
import os
import re
import tempfile

import requests
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth
import voluptuous as vol

from homeassistant.components.notify import (
    ATTR_TITLE, ATTR_TITLE_DEFAULT, ATTR_TARGET, ATTR_DATA,
    BaseNotificationService)
from homeassistant.const import CONF_API_KEY
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['python-pushover==0.4']
_LOGGER = logging.getLogger(__name__)

# Top level attributes in 'data'
ATTR_FILE = 'file'

# Attributes contained in file
ATTR_FILE_URL = 'url'
ATTR_FILE_PATH = 'path'
ATTR_FILE_USERNAME = 'username'
ATTR_FILE_PASSWORD = 'password'
ATTR_FILE_AUTH = 'auth'

# Valid values for 'auth' attribute
ATTR_FILE_AUTH_BASIC = 'basic'
ATTR_FILE_AUTH_DIGEST = 'digest'

CONF_TIMEOUT = 15
CONF_USER_KEY = 'user_key'

PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USER_KEY): cv.string,
    vol.Required(CONF_API_KEY): cv.string,
})


def get_service(hass, config, discovery_info=None):
    """Get the Pushover notification service."""
    from pushover import InitError

    try:
        return PushoverNotificationService(
            config[CONF_USER_KEY], config[CONF_API_KEY])
    except InitError:
        _LOGGER.error("Wrong API key supplied")
        return None


class PushoverNotificationService(BaseNotificationService):
    """Implement the notification service for Pushover."""

    def __init__(self, user_key, api_token):
        """Initialize the service."""
        from pushover import Client
        self._user_key = user_key
        self._api_token = api_token
        self.pushover = Client(
            self._user_key, api_token=self._api_token)

    def send_message(self, message='', **kwargs):
        """Send a message to a user."""
        from pushover import RequestError

        # Make a copy and use empty dict if necessary
        data = dict(kwargs.get(ATTR_DATA) or {})
        file_data = data.pop(ATTR_FILE, None)

        data['title'] = kwargs.get(ATTR_TITLE, ATTR_TITLE_DEFAULT)

        targets = kwargs.get(ATTR_TARGET)

        if not isinstance(targets, list):
            targets = [targets]

        file = {}

        if file_data is not None:
            filename = self.load_file(
                url=file_data.get(ATTR_FILE_URL),
                username=file_data.get(ATTR_FILE_USERNAME),
                password=file_data.get(ATTR_FILE_PASSWORD),
                auth=file_data.get(ATTR_FILE_AUTH))

            if filename is not None:
                file = (filename, open(
                    filename, "rb"), mimetypes.guess_type(filename))

        for target in targets:
            if target is not None:
                data['device'] = target

            try:
                self.pushover.send_message(message=message, attachment=file, **data)
            except ValueError as val_err:
                _LOGGER.error(str(val_err))
            except RequestError:
                _LOGGER.exception("Could not send pushover notification")

    def load_file(self, url=None, username=None, password=None, auth=None):
        """Load image/document/etc from a local path or URL."""

        # Check whether authentication parameters are provided
        if username:
            # Use digest or basic authentication
            if ATTR_FILE_AUTH_DIGEST == auth:
                auth = HTTPDigestAuth(username, password)
            else:
                auth = HTTPBasicAuth(username, password)
        else:
            auth = None

        # Make the request and raise an error if necessary
        try:
            if auth:
                response = requests.get(url, auth=auth, timeout=CONF_TIMEOUT)
            else:
                response = requests.get(url, timeout=CONF_TIMEOUT)

            response.raise_for_status()
        except requests.exceptions.RequestException as request_error:
            _LOGGER.error("Can't load from url: %s", request_error)

        downloaded_file = (
            tempfile.NamedTemporaryFile(delete=False)
        )

        try:
            filename = downloaded_file.name
            downloaded_file.write(response.content)
        except OSError as error:
            _LOGGER.error("Can't load from url or local path: %s", error)

        return filename
