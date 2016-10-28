import os
import select
import sys

import argparse
import json
import logging.config
import pkg_resources
import threading
import tty


LOG = None
LOG_LEVELS = ['debug', 'info', 'warn', 'error']


def get_config():
    constants = dict(os.environ)
    if pkg_resources.resource_exists(__name__, 'config.json'):
        raw = pkg_resources.resource_string(__name__, 'config.json')
        constants.update(json.loads(raw))
    return constants


def main():
    """ Run a worker that manages a Raspberry Pi """
    global LOG
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('-H', '--host', default='localhost',
                        help="Webserver host (default %(default)s)")
    parser.add_argument('-p', '--port', type=int, default=8080,
                        help="Webserver port (default %(default)d)")
    parser.add_argument('-d', '--debug', action='store_true',
                        help="Don't send/receive signals from GPIO")
    parser.add_argument('-l', default='warn', choices=LOG_LEVELS,
                        help="Log level (default %(default)s)")
    parser.add_argument('-f', help="Log file")
    parser.add_argument('-i', action='store_true',
                        help="Interactive mode")
    args = parser.parse_args()

    log_config = {
        'version': 1,
        'formatters': {
            'brief': {
                'format': "%(asctime)s %(levelname)7s [%(name)s]: %(message)s",
                'datefmt': "%Y-%m-%d %H:%M:%S",
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'brief',
                'stream': 'ext://sys.stdout',
            },
        },
        'root': {
            'level': args.l.upper(),
            'handlers': [
                'console',
            ],
        },
    }
    if args.f is not None:
        log_config['root']['handlers'].append('file')
        log_config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'brief',
            'filename': args.f,
            'maxBytes': 1024 * 1024,
            'backupCount': 3,
        }
    logging.config.dictConfig(log_config)
    LOG = logging.getLogger(__name__)

    # Import these after we've finished setting up logging
    from .gutil import Calendar
    from .web import run_webserver
    from .worker import DoorWorker

    config = get_config()
    client_id = config['STINY_SERVER_GOOGLE_CLIENT_ID']
    client_secret = config['STINY_SERVER_GOOGLE_CLIENT_SECRET']
    calendar_id = config['STINY_CAL_ID']
    calendar = Calendar(client_id, client_secret, calendar_id=calendar_id)

    # Start the worker
    worker = DoorWorker(calendar=calendar, isolate=args.debug)
    worker.daemon = True
    worker.start()

    if args.i:
        web_thread = threading.Thread(target=run_webserver,
                                      args=[worker, args.host, args.port])
        web_thread.daemon = True
        web_thread.start()
        poll_user_input(worker)
    else:
        run_webserver(worker, args.host, args.port)


def poll_user_input(worker):
    tty.setcbreak(sys.stdin)
    input_names = worker.get_inputs()
    input_states = {name: False for name in input_names}
    for i, name in enumerate(input_names):
        print "%d: %s" % (i + 1, name)
    while True:
        key = get_keypress()
        if key is not None:
            if key.isdigit():
                idx = int(key) - 1
                if 0 <= idx < len(input_names):
                    name = input_names[idx]
                    input_states[name] = not input_states[name]
                    worker.trigger_input(name, input_states[name])


def get_keypress():
    i, o, e = select.select([sys.stdin], [], [], 0.0001)
    for s in i:
        if s == sys.stdin:
            return sys.stdin.read(1)
    return None

if __name__ == '__main__':
    main()
