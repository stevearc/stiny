import os

import argparse
from datetime import timedelta
from pprint import pprint

from .gutil import Calendar


def do_calendar():
    """ List calendar events for debugging purposes """
    parser = argparse.ArgumentParser(description=do_calendar.__doc__)
    parser.add_argument(
        '-p',
        type=int,
        default=0,
        help="Number of days in the past to search (default %(default)s)")
    parser.add_argument(
        '-f',
        type=int,
        default=0,
        help="Number of days in the future to search (default %(default)s)")
    args = parser.parse_args()

    client_id = os.environ['STINY_SERVER_GOOGLE_CLIENT_ID']
    client_secret = os.environ['STINY_SERVER_GOOGLE_CLIENT_SECRET']
    calendar = Calendar(client_id, client_secret)

    past = timedelta(days=args.p, minutes=5)
    future = timedelta(days=args.f, minutes=5)
    for event in calendar.iter_active_events(past, future):
        print '-' * 20
        pprint(event)
