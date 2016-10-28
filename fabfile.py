import os

import fabric.api as fab
import jinja2
import json
from fabric.context_managers import path
from fabric.decorators import roles
from pyramid.settings import aslist
from stiny.gutil import normalize_email


fab.env.roledefs = {
    'door': ['pi@192.168.86.200'],
    'web': ['stevearc@stevearc.com'],
}


def _version():
    return fab.local('git describe --tags', capture=True)


def _get_ref():
    ref = fab.local('git rev-parse HEAD', capture=True)
    return ref[:8]


def _get_var(key):
    if key not in os.environ:
        raise Exception("Missing environment variable %r" % key)
    return os.environ[key]

CONSTANTS = {
    'venv': '/envs/stiny',
    'admins': [normalize_email(e) for e in aslist(_get_var('STINY_ADMINS'))],
    'guests': [normalize_email(e) for e in aslist(_get_var('STINY_GUESTS'))],
    'phone_access': _get_var('STINY_PHONE_ACCESS'),
    'url_prefix': 'gen/' + _get_ref(),
    'session': {
        'encrypt_key': _get_var('STINY_ENCRYPT_KEY'),
        'validate_key': _get_var('STINY_VALIDATE_KEY'),
    },
    'authtkt': {
        'secret': _get_var('STINY_AUTH_SECRET'),
    },
    'google': {
        'client_id': _get_var('STINY_PROD_CLIENT_GOOGLE_CLIENT_ID'),
        'server_client_id': _get_var('STINY_SERVER_GOOGLE_CLIENT_ID'),
        'server_client_secret': _get_var('STINY_SERVER_GOOGLE_CLIENT_SECRET'),
        'calendar_id': _get_var('STINY_CAL_ID'),
    },
    'twilio': {
        'auth_token': _get_var('STINY_TWILIO_AUTH_TOKEN'),
    }
}


def _render(filename, **context):
    with open(filename, 'r') as ifile:
        tmpl = jinja2.Template(ifile.read())
    basename = os.path.basename(filename)
    fab.local('mkdir -p dist')
    outfile = os.path.join('dist', basename)
    with open(outfile, 'w') as ofile:
        ofile.write(tmpl.render(**context))
    return outfile


def _render_put(filename, dest, **kwargs):
    rendered = _render(filename, **CONSTANTS)
    fab.put(rendered, dest, **kwargs)


def write_credentials(filename):
    from stiny.gutil import Calendar
    google = CONSTANTS['google']
    cal = Calendar(google['server_client_id'], google['server_client_secret'],
                   filename, calendar_id=google['calendar_id'])
    cal.login_if_needed()


def build_web():
    fab.local('npm install')
    fab.local('rm -rf stiny/webpack')
    fab.local('npm run flow')
    fab.local('npm run build-prod')
    version = _version()
    fab.local("sed -i -e 's/version=.*/version=\"%s\",/' setup.py" % version)
    write_credentials('stiny/credentials.dat')
    fab.local('python setup.py sdist')
    fab.local("sed -i -e 's/version=.*/version=\"develop\",/' setup.py")
    _render('prod.ini.tmpl', **CONSTANTS)
    print "Created dist/stiny-%s.tar.gz" % version
    return version


@roles('web')
def deploy_web():
    version = build_web()
    tarball = "stiny-%s.tar.gz" % version
    fab.put("dist/" + tarball)
    fab.sudo("if [ ! -e {0} ]; then virtualenv {0}; fi"
             .format(CONSTANTS['venv']))
    with path(CONSTANTS['venv'] + '/bin', behavior='prepend'):
        fab.sudo("yes | pip uninstall stiny || true")
        fab.sudo("pip install pastescript")
        fab.sudo("pip install %s" % tarball)
    _render_put('prod.ini.tmpl', '/etc/emperor/stiny.ini', use_sudo=True)


@roles('door')
def build_rpi_gpio_wheel():
    gpio_wheel = 'RPi.GPIO-0.6.2-cp27-cp27mu-linux_armv6l.whl'
    fab.local('mkdir -p pex_wheels')
    # Generate the RPI.GPIO wheel on the raspberry pi
    fab.run('rm -rf /tmp/gpiobuild')
    fab.run('mkdir -p /tmp/gpiobuild')
    with fab.cd('/tmp/gpiobuild'):
        fab.run('virtualenv venv')
        with path('/tmp/gpiobuild/venv/bin', behavior='prepend'):
            fab.run('pip install wheel')
            fab.run('pip wheel RPi.GPIO==0.6.2 --wheel-dir=/tmp/gpiobuild')
            fab.get(gpio_wheel, os.path.join('pex_wheels', gpio_wheel))
    fab.run('rm -rf /tmp/gpiobuild')


def build_door():
    fab.local('rm -f dist/stiny')
    constants = ['STINY_SERVER_GOOGLE_CLIENT_ID',
                 'STINY_SERVER_GOOGLE_CLIENT_SECRET', 'STINY_CAL_ID']
    config = {}
    for key in constants:
        config[key] = _get_var(key)
    with open('stiny_worker/stiny_worker/config.json', 'w') as ofile:
        json.dump(config, ofile)
    write_credentials('stiny_worker/stiny_worker/credentials.dat')

    gpio_wheel = 'RPi.GPIO-0.6.2-cp27-cp27mu-linux_armv6l.whl'
    if not os.path.exists(os.path.join('pex_wheels', gpio_wheel)):
        fab.execute(build_rpi_gpio_wheel)

    fab.local('rm -f pex_cache/stiny_worker-develop-py2-none-any.whl')
    fab.local('pex -vvvv --platform=linux_armv6l -f pex_wheels '
              '--cache-dir=pex_cache '
              'stiny_worker -m stiny_worker:main -o dist/stiny')


@roles('door')
def deploy_door():
    build_door()
    fab.put("dist/stiny")
    fab.put("stiny-service", "/etc/init.d/stiny", use_sudo=True, mode=744)
    fab.put("stiny-tunnel-service", "/etc/init.d/stiny-tunnel", use_sudo=True,
            mode=744)
    fab.sudo("service stiny-tunnel restart")
    fab.sudo("service stiny restart")
