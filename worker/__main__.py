import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from distutils.spawn import find_executable  # pylint: disable=E0611,F0401

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


LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warn': logging.WARN,
    'error': logging.ERROR,
}

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
    parser.add_argument('-l', default='warn', choices=LOG_LEVELS.keys(),
                        help="Log level (default %(default)s)")
    args = parser.parse_args()

    logging.basicConfig()
    logging.getLogger().setLevel(LOG_LEVELS[args.l])

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

    # Set up the bottle endpoint
    from bottle import route, request, run

    @route('/do/<command>', method='POST')
    def do_command(command):
        kwargs = dict(request.json)
        worker.do(command, **kwargs)
        return {}

    run(host=args.host, port=args.port)


if __name__ == '__main__':
    main()
