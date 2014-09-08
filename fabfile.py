import fabric.api as fab
from fabric.decorators import roles
import os
from base64 import b64encode

fab.env.roledefs = {
    'pi': ['pi@10.0.1.200'],
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

def bundle():
    fab.local('./dl-deps.sh')
    fab.local('rm -rf stiny/gen')
    fab.local('go run build.go')
    ref = fab.local('git rev-parse --verify HEAD', capture=True)
    fab.local('cp prod.ini.tmpl prod.ini')

    fab.local("sed -i -e 's/URL_PREFIX/gen\\/%s/' prod.ini" % ref[:8])
    _set_var('prod.ini', 'session.encrypt_key', _get_var('STINY_ENCRYPT_KEY'))
    _set_var('prod.ini', 'session.validate_key', _get_var('STINY_VALIDATE_KEY'))
    _set_var('prod.ini', 'authtkt.secret', _get_var('STINY_AUTH_SECRET'))
    _set_var('prod.ini', 'google.client_id', _get_var('STINY_GOOGLE_CLIENT_ID'))

    version = _version()
    fab.local("sed -i -e 's/version=.*/version=\"%s\",/' setup.py" % version)
    fab.local('python setup.py sdist')
    print "Created dist/stiny-%s.tar.gz" % version


@roles('pi')
def deploy():
    bundle()
    version = _version()
    tarball = "stiny-%s.tar.gz" % version
    fab.put("dist/" + tarball)
    fab.run("if [ ! -e stiny_env ]; then virtualenv stiny_env; fi")
    fab.run("./stiny_env/bin/pip install waitress")
    fab.run("yes | ./stiny_env/bin/pip uninstall stiny")
    fab.run("./stiny_env/bin/pip install " + tarball)
    fab.put("prod.ini")
    fab.sudo("service stiny restart")
