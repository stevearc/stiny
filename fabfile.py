import os

import fabric.api as fab
from fabric.context_managers import lcd
from fabric.decorators import roles


fab.env.roledefs = {
    'pi': ['pi@10.0.1.200'],
    'nimbus': ['stevearc@stevearc.com'],
}


def _version():
    return fab.local('git describe --tags', capture=True)


def _get_var(key):
    if key not in os.environ:
        raise Exception("Missing environment variable %r" % key)
    return os.environ[key]


def _set_var(filename, name, value):
    fab.local("sed -i -e 's/%s.*/%s = %s/' %s" %
              (name, name, value.replace('/', '\\/'), filename))


def create_prod_config(name):
    fab.local('cp prod.ini.tmpl %s' % name)

    ref = fab.local('git rev-parse --verify HEAD', capture=True)
    fab.local("sed -i -e 's/URL_PREFIX/gen\\/%s/' %s" % (ref[:8], name))
    _set_var(name, 'session.encrypt_key', _get_var('STINY_ENCRYPT_KEY'))
    _set_var(name, 'session.validate_key',
             _get_var('STINY_VALIDATE_KEY'))
    _set_var(name, 'authtkt.secret', _get_var('STINY_AUTH_SECRET'))
    _set_var(name, 'google.client_id',
             _get_var('STINY_GOOGLE_CLIENT_ID'))
    _set_var(name, 'google.server_client_id',
             _get_var('STINY_SERVER_GOOGLE_CLIENT_ID'))
    _set_var(name, 'google.server_client_secret',
             _get_var('STINY_SERVER_GOOGLE_CLIENT_SECRET'))
    _set_var(name, 'twilio.auth_token',
             _get_var('STINY_TWILIO_AUTH_TOKEN'))


def write_credentials(filename):
    from stiny.gutil import Calendar
    client_id = _get_var('STINY_SERVER_GOOGLE_CLIENT_ID')
    client_secret = _get_var('STINY_SERVER_GOOGLE_CLIENT_SECRET')
    Calendar(client_id, client_secret, filename)


def bundle_web():
    fab.local('./dl-deps.sh')
    fab.local('rm -rf stiny/gen')
    fab.local('go run build.go')
    version = _version()
    fab.local("sed -i -e 's/version=.*/version=\"%s\",/' setup.py" % version)
    write_credentials('credentials.dat')
    fab.local('cp credentials.dat stiny')
    fab.local('python setup.py sdist')
    print "Created dist/stiny-%s.tar.gz" % version


@roles('nimbus')
def deploy_web():
    bundle_web()
    version = _version()
    tarball = "stiny-%s.tar.gz" % version
    fab.put("dist/" + tarball)
    venv = "/envs/stiny"
    create_prod_config('prod.ini')
    fab.sudo("yes | %s/bin/pip uninstall stiny || true" % venv)
    fab.sudo("%s/bin/pip install pastescript" % venv)
    fab.sudo("%s/bin/pip install %s" % (venv, tarball))
    fab.put('prod.ini', '/etc/emperor/stiny.ini', use_sudo=True)


def bundle_door():
    fab.local('mkdir -p build')
    fab.local('rm -rf build/worker')
    fab.local('rm -f build/worker.zip')
    fab.local('cp -rL worker build/worker')
    write_credentials('credentials.dat')
    fab.local('cp credentials.dat build/worker')
    constants = ['STINY_SERVER_GOOGLE_CLIENT_ID', 'STINY_SERVER_GOOGLE_CLIENT_SECRET']
    with open('build/worker/credentials.py', 'w') as ofile:
        for c in constants:
            ofile.write("%s = '%s'\n" % (c, _get_var(c)))
    files = [f for f in os.listdir('build/worker') if f.split('.')[-1] in ('py', 'dat')]
    with lcd('build/worker'):
        fab.local('zip ../worker.zip %s' % (' '.join(files)))
    fab.local('rm -rf build/worker')


@roles('pi')
def deploy_door():
    bundle_door()
    fab.put("build/worker.zip")
    fab.put("stiny-service", "/etc/init.d/stiny", use_sudo=True, mode=744)
    fab.put("stiny-tunnel-service", "/etc/init.d/stiny-tunnel", use_sudo=True,
            mode=744)
    fab.sudo("service stiny-tunnel restart")
    fab.sudo("service stiny restart")
