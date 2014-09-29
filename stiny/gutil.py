import gflags
import httplib2
import pkg_resources
from apiclient.discovery import build
from datetime import datetime, timedelta
from oauth2client.client import OAuth2WebServerFlow, Credentials
from oauth2client.file import Storage as BaseStorage
from oauth2client.tools import run


FLAGS = gflags.FLAGS

# EMS calendar id
CAL_ID = 'klpl9hfdirojidnukjkbpbq50c@group.calendar.google.com'


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
        credentials = storage.get()
        if credentials is None or credentials.invalid:
            credentials = run(FLOW, storage)

        http = httplib2.Http()
        http = credentials.authorize(http)
        self._service = build(serviceName='calendar', version='v3', http=http)

    def iter_events(self, start=None, end=None):
        events = self._service.events()
        req = events.list(calendarId=CAL_ID, timeMin=dump_dt(start),
                          timeMax=dump_dt(end))
        response = req.execute()
        events = response['items']
        for event in events:
            yield event

    def iter_active_events(self, past=timedelta(minutes=5),
                           future=timedelta(minutes=5)):
        now = datetime.utcnow()
        return self.iter_events(now - past, now + future)

    def is_party_time(self):
        for event in self.iter_active_events():
            if 'party' in event['summary'].lower():
                return True
        return False

    def is_guest(self, email):
        email = email.lower()
        for event in self.iter_active_events():
            description = event['description'].split('\n')
            for line in description:
                line = line.lower().strip()
                if line.startswith('guest:'):
                    guest_email = line.split(':')[1].strip()
                    if email == guest_email:
                        return True
        return False
