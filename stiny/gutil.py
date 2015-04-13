import re

import gflags
import httplib2
import logging
import pkg_resources
from apiclient.discovery import build
from datetime import datetime, timedelta
from oauth2client.client import OAuth2WebServerFlow, Credentials
from oauth2client.file import Storage as BaseStorage
from oauth2client.tools import run


LOG = logging.getLogger(__name__)
FLAGS = gflags.FLAGS

# EMS calendar id
CAL_ID = 'klpl9hfdirojidnukjkbpbq50c@group.calendar.google.com'

REFRESH_MINS = timedelta(minutes=15)


def dump_dt(dt):
    if dt is None:
        return None
    return dt.isoformat('T') + 'Z'


class Storage(BaseStorage):

    def locked_get(self):
        credentials = None
        if not pkg_resources.resource_exists(__name__, self._filename):
            return super(Storage, self).locked_get()
        content = pkg_resources.resource_string(__name__, self._filename)
        credentials = Credentials.new_from_json(content)
        credentials.set_store(self)
        return credentials


class Calendar(object):

    def __init__(
            self,
            client_id,
            client_secret,
            credential_file='credentials.dat'):
        FLOW = OAuth2WebServerFlow(
            client_id,
            client_secret,
            scope='https://www.googleapis.com/auth/calendar.readonly',
            redirect_uri='urn:ietf:wg:oauth:2.0:oob',
            user_agent='stiny/0.1')

        FLAGS.auth_local_webserver = False
        storage = Storage(credential_file)
        self.credentials = storage.get()
        if self.credentials is None or self.credentials.invalid:
            self.credentials = run(FLOW, storage)

        http = httplib2.Http()
        self.http = self.credentials.authorize(http)
        self._service = build(serviceName='calendar', version='v3', http=self.http)

    def _refresh_credentials_if_needed(self):
        if self.credentials.token_expiry - datetime.utcnow() < REFRESH_MINS:
            LOG.info("Refreshing OAUTH2 credentials")
            self.credentials.refresh(self.http)

    @property
    def service(self):
        self._refresh_credentials_if_needed()
        return self._service

    def iter_events(self, start=None, end=None):
        events = self.service.events()
        req = events.list(calendarId=CAL_ID, timeMin=dump_dt(start),
                          timeMax=dump_dt(end))
        response = req.execute()
        events = response['items']
        for event in events:
            yield event

    def iter_active_events(self, past=timedelta(minutes=1),
                           future=timedelta()):
        # TODO: this does not handle all-day events because those are stored
        # with no knowledge of any timezone.
        now = datetime.utcnow()
        return self.iter_events(now - past, now + future)

    def is_party_time(self):
        for event in self.iter_active_events():
            if 'party' in event['summary'].lower():
                return True
        return False

    def _iter_event_lines(self):
        for event in self.iter_active_events():
            description = event.get('description', '').strip()
            if description:
                for line in description.split('\n'):
                    yield line

    def _iter_event_guest_tokens(self):
        for line in self._iter_event_lines():
            if line.startswith('guest:'):
                for token in line[6:].lower().split(','):
                    yield token.strip()

    def is_email_guest(self, email):
        return email in self._iter_event_guest_tokens()

    def is_phone_guest(self, number):
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
        if token.isdigit():
            return self.is_phone_guest(token)
        else:
            return self.is_email_guest(token)
