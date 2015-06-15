""" Google Calendar utility """
import re

import argparse
import httplib2
import logging
import pkg_resources
from apiclient.discovery import build  # pylint: disable=F0401
from datetime import datetime, timedelta
from oauth2client.client import (OAuth2WebServerFlow, Credentials,
                                 AccessTokenCredentialsError)
from oauth2client.file import Storage as BaseStorage
from oauth2client.tools import run_flow, argparser


LOG = logging.getLogger(__name__)

REFRESH_MINS = timedelta(minutes=15)


def dump_dt(dt):
    """ Dump a naive datetime to UTC format """
    if dt is None:
        return None
    return dt.isoformat('T') + 'Z'


class Storage(BaseStorage):
    """ Credential storage that can load from a python package resource. """

    def locked_get(self):
        credentials = None
        if not pkg_resources.resource_exists(__name__, self._filename):
            return super(Storage, self).locked_get()
        content = pkg_resources.resource_string(__name__, self._filename)
        credentials = Credentials.new_from_json(content)
        credentials.set_store(self)
        return credentials


class Calendar(object):
    """ Google Calendar API wrapper class """

    def __init__(
            self,
            client_id,
            client_secret,
            credential_file='credentials.dat',
            flags=None,
            calendar_id=None):
        self.calendar_id = calendar_id
        if flags is None:
            parser = argparse.ArgumentParser(parents=[argparser])
            flags = parser.parse_args([])
        self._client_id = client_id
        self._client_secret = client_secret
        self._flags = flags

        self._storage = Storage(credential_file)
        self.credentials = self._storage.get()
        self._http = None
        self._service = None

    def login_if_needed(self):
        """ If API credentials not found in storage, do web login """
        if not self.is_credentials_valid:
            flow = OAuth2WebServerFlow(
                self._client_id,
                self._client_secret,
                scope='https://www.googleapis.com/auth/calendar.readonly',
                redirect_uri='urn:ietf:wg:oauth:2.0:oob',
                user_agent='stiny/0.1')
            self.credentials = run_flow(flow, self._storage, self._flags)

    def _refresh_credentials_if_needed(self):
        """ If credentials will expire soon, force a refresh """
        if not self.is_credentials_valid:
            raise AccessTokenCredentialsError("Invalid google credentials")
        if self.credentials.token_expiry - datetime.utcnow() < REFRESH_MINS:
            LOG.info("Refreshing OAUTH2 credentials")
            self.credentials.refresh(self.http)

    @property
    def is_credentials_valid(self):
        """ True if the oauth credentials are valid """
        return self.credentials is not None and not self.credentials.invalid

    @property
    def http(self):
        """ Accessor for authorized http object """
        if self._http is None:
            if not self.is_credentials_valid:
                raise AccessTokenCredentialsError("Invalid google credentials")
            http = httplib2.Http()
            self._http = self.credentials.authorize(http)
        return self._http

    @property
    def service(self):
        """ Convenience property for Calendar service that refreshes tokens """
        self._refresh_credentials_if_needed()
        if self._service is None:
            self._service = build(
                serviceName='calendar',
                version='v3',
                http=self.http)
        return self._service

    def iter_events(self, start=None, end=None):
        """ Generator that iterates over all Calendar events in a range """
        events = self.service.events()
        req = events.list(calendarId=self.calendar_id, timeMin=dump_dt(start),
                          timeMax=dump_dt(end))
        response = req.execute()
        events = response['items']
        for event in events:
            yield event

    def iter_active_events(self, past=timedelta(minutes=1),
                           future=timedelta()):
        """ Generator that iterates over all active calendar events """
        # TODO: this does not handle all-day events because those are stored
        # with no knowledge of any timezone.
        now = datetime.utcnow()
        return self.iter_events(now - past, now + future)

    def is_party_time(self):
        """ Check if there is an active party event """
        for event in self.iter_active_events():
            if 'party' in event['summary'].lower():
                return True
        return False

    def _iter_event_lines(self):
        """ Iterate over all lines in the description of an event """
        for event in self.iter_active_events():
            description = event.get('description', '').strip()
            if description:
                for line in description.split('\n'):
                    yield line

    def _iter_event_guest_tokens(self):
        """ Iterate over all comma-separated values in all 'guest:' lines """
        for line in self._iter_event_lines():
            if line.startswith('guest:'):
                for token in line[6:].lower().split(','):
                    yield token.strip()

    def is_email_guest(self, email):
        """ Check if an email address has guest permissions """
        return email in self._iter_event_guest_tokens()

    def is_phone_guest(self, number):
        """ Check if a phone number has guest permissions """
        for token in self._iter_event_guest_tokens():
            trimmed = re.sub(r'[^\d]', '', token)
            if number == trimmed:
                return True
        return False

    def is_guest(self, token):
        """
        Check if someone is a guest

        Parameters
        ----------
        token : str
            This can be anything, but right now we are only checking emails
            (web interface) and phone numbers (twilio).

        """
        # Trim off the country code for phone numbers
        if token.startswith('+1'):
            token = token[2:]
        if token.isdigit():
            return self.is_phone_guest(token)
        else:
            return self.is_email_guest(token)
