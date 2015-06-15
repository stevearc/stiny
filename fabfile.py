import os
from pyramid.settings import aslist
import jinja2

import fabric.api as fab
from fabric.context_managers import lcd, path
from fabric.decorators import roles


fab.env.roledefs = {
    'pi': ['pi@10.0.1.200'],
    'nimbus': ['stevearc@stevearc.com'],
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
    'admins': aslist(_get_var('STINY_ADMINS')),
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
        'client_id': _get_var('STINY_GOOGLE_CLIENT_ID'),
        'server_client_id': _get_var('STINY_SERVER_GOOGLE_CLIENT_ID'),
        'server_client_secret': _get_var('STINY_SERVER_GOOGLE_CLIENT_SECRET'),
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
    Calendar(google['server_client_id'], google['server_client_secret'], filename)
    cal.login_if_needed()


def bundle_web():
    fab.local('./dl-deps.sh')
    fab.local('rm -rf stiny/gen')
    fab.local('go run build.go')
    version = _version()
    fab.local("sed -i -e 's/version=.*/version=\"%s\",/' setup.py" % version)
    write_credentials('credentials.dat')
    fab.local('cp credentials.dat stiny')
    fab.local('python setup.py sdist')
    fab.local("sed -i -e 's/version=.*/version=\"develop\",/' setup.py")
    _render('prod.ini.tmpl', **CONSTANTS)
    print "Created dist/stiny-%s.tar.gz" % version
    return version


@roles('nimbus')
def deploy_web():
    version = bundle_web()
    tarball = "stiny-%s.tar.gz" % version
    fab.put("dist/" + tarball)
    with path(CONSTANTS['venv'] + '/bin', behavior='prepend'):
        fab.sudo("yes | pip uninstall stiny || true")
        fab.sudo("pip install pastescript")
        fab.sudo("pip install %s" % tarball)
    _render_put('prod.ini.tmpl', '/etc/emperor/stiny.ini', use_sudo=True)


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
