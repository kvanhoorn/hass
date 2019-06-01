"""Pushover platform for notify component."""
import logging
import re

import requests
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth
import voluptuous as vol

from homeassistant.const import CONF_API_KEY
import homeassistant.helpers.config_validation as cv

from homeassistant.components.notify import (
    ATTR_DATA, ATTR_TARGET, ATTR_TITLE, ATTR_TITLE_DEFAULT, PLATFORM_SCHEMA,
    BaseNotificationService)

_LOGGER = logging.getLogger(__name__)

# Top level attributes in 'data'
ATTR_FILE = 'file'

# Attributes contained in file
ATTR_FILE_PATH = 'path'
ATTR_FILE_URL = 'url'
ATTR_FILE_AUTH = 'auth'
ATTR_FILE_USERNAME = 'username'
ATTR_FILE_PASSWORD = 'password'

# Valid values for 'auth' attribute
ATTR_FILE_AUTH_BASIC = 'basic'
ATTR_FILE_AUTH_DIGEST = 'digest'

CONF_TIMEOUT = 15
CONF_USER_KEY = 'user_key'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USER_KEY): cv.string,
    vol.Required(CONF_API_KEY): cv.string,
})


def get_service(hass, config, discovery_info=None):
    """Get the Pushover notification service."""
    from pushover import InitError

    try:
        return PushoverNotificationService(
            config[CONF_USER_KEY], config[CONF_API_KEY],
            hass.config.is_allowed_path, hass.config.path('www'))
    except InitError:
        _LOGGER.error("Wrong API key supplied")
        return None


class PushoverNotificationService(BaseNotificationService):
    """Implement the notification service for Pushover."""

    def __init__(self, user_key, api_token, is_allowed_path, local_www_path):
        """Initialize the service."""
        from pushover import Client
        self._user_key = user_key
        self._api_token = api_token
        self._is_allowed_path = is_allowed_path
        self._local_www_path = local_www_path
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
            file = self.load_file(
                url=file_data.get(ATTR_FILE_URL),
                local_path=file_data.get(ATTR_FILE_PATH),
                username=file_data.get(ATTR_FILE_USERNAME),
                password=file_data.get(ATTR_FILE_PASSWORD),
                auth=file_data.get(ATTR_FILE_AUTH))

        for target in targets:
            if target is not None:
                data['device'] = target

            try:
                self.pushover.send_message(
                    message=message, attachment=file, **data)

            except ValueError as val_err:
                _LOGGER.error(str(val_err))
            except RequestError:
                _LOGGER.exception("Could not send pushover notification")

    def load_file(self, url=None, local_path=None, username=None,
                  password=None, auth=None):
        """Load image/document/etc from a local path or URL."""
        # Load the file from URL
        if url:
            if username:
                if ATTR_FILE_AUTH_DIGEST == auth:
                    auth = HTTPDigestAuth(username, password)
                else:
                    auth = HTTPBasicAuth(username, password)
            else:
                auth = None

            # Make the request and raise an error if necessary
            try:
                response = requests.get(url, auth=auth, timeout=CONF_TIMEOUT)
                response.raise_for_status()
                return response.content

            except requests.exceptions.RequestException as request_error:
                _LOGGER.error("Could not load from url: %s", request_error)

        # Load the file from the filesystem
        elif local_path:
            # Change the path if the file is in the local www directory
            regex = re.compile('^/local/')
            local_path = regex.sub(self._local_www_path + "/", local_path)

            # Check whether path is whitelisted in configuration.yaml
            if self._is_allowed_path(local_path):
                try:
                    return open(local_path, "rb")
                except OSError as error:
                    _LOGGER.error("Could not load file: %s", error)
            else:
                _LOGGER.warning("Could not load file from insecure path: '%s'",
                                local_path)
        else:
            _LOGGER.warning("Neither URL nor local path found in params!")

        return None