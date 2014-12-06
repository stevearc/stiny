import os
import select
import sys
from distutils.spawn import find_executable  # pylint: disable=E0611,F0401

import argparse
import logging
import logging.config
import shutil
import subprocess
import tempfile
import threading
import tty


LOG = None


try:
    from urllib import urlretrieve
except ImportError:
    from urllib.request import urlretrieve  # pylint: disable=E0611,F0401

VENV_VERSION = '1.11.6'
VENV_URL = ("https://pypi.python.org/packages/source/v/"
            "virtualenv/virtualenv-%s.tar.gz" % VENV_VERSION)
VENV_NAME = 'myvirtualenv'
DEPENDENCIES = {
    'RPi.GPIO': 'rpi.gpio',
    'bottle': 'bottle',
    'oauth2client': 'google-api-python-client',
    'gflags': 'python-gflags',
}


def bootstrap_virtualenv(env):
    """
    Activate a virtualenv, creating it if necessary.

    Parameters
    ----------
    env : str
        Path to the virtualenv

    """
    if not os.path.exists(env):
        # If virtualenv command exists, use that
        if find_executable('virtualenv') is not None:
            cmd = ['virtualenv'] + [env]
            subprocess.check_call(cmd)
        else:
            # Otherwise, download virtualenv from pypi
            path = urlretrieve(VENV_URL)[0]
            subprocess.check_call(['tar', 'xzf', path])
            subprocess.check_call(
                [sys.executable,
                 "virtualenv-%s/virtualenv.py" % VENV_VERSION,
                 env])
            os.unlink(path)
            shutil.rmtree("virtualenv-%s" % VENV_VERSION)
        print("Created virtualenv %s" % env)

    executable = os.path.join(env, 'bin', 'python')
    os.execv(executable, [executable] + sys.argv)


def is_inside_virtualenv(env):
    return any((p.startswith(env) for p in sys.path))


def install_lib(venv, name, pip_name=None):
    try:
        __import__(name)
    except ImportError:
        if pip_name is None:
            pip_name = name
        pip = os.path.join(venv, 'bin', 'pip')
        subprocess.check_call([pip, 'install', pip_name])
    except RuntimeError as e:
        LOG.warn("Error when importing library: %s", e)


def get_constant(constant):
    if constant in os.environ:
        return os.environ[constant]
    else:
        import credentials
        return getattr(credentials, constant)


LOG_LEVELS = ['debug', 'info', 'warn', 'error']

def main():
    """ Run a worker that manages a Raspberry Pi """
    global LOG
    parser = argparse.ArgumentParser(description=main.__doc__)
    default_env = os.path.join(tempfile.gettempdir(), VENV_NAME)
    parser.add_argument('-e', default=default_env,
                        help="Path to virtualenv (default %(default)s)")
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
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'brief',
                'filename': args.f,
                'maxBytes': 1024 * 1024,
                'backupCount': 3,
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
    logging.config.dictConfig(log_config)

    LOG = logging.getLogger(__name__)

    # Install or restart into virtualenv if necessary
    if not is_inside_virtualenv(args.e):
        bootstrap_virtualenv(args.e)
        return
    for name, pip_name in DEPENDENCIES.items():
        install_lib(args.e, name, pip_name)

    # Connect to Dynamodb
    from gutil import Calendar

    client_id = get_constant('STINY_SERVER_GOOGLE_CLIENT_ID')
    client_secret = get_constant('STINY_SERVER_GOOGLE_CLIENT_SECRET')
    calendar = Calendar(client_id, client_secret)

    # Start the worker
    from worker import DoorWorker
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


def run_webserver(worker, host, port):
    # Set up the bottle endpoint
    from bottle import route, request, run

    @route('/do/<command>', method='POST')
    def do_command(command):
        kwargs = dict(request.json)
        worker.do(command, **kwargs)
        return {}

    run(host=host, port=port)


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
