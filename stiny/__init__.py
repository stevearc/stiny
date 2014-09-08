import calendar
from flywheel import Engine
from .models import UserPerm
import json
import os
import posixpath
from collections import defaultdict

import datetime
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Authenticated
from pyramid.config import Configurator
from pyramid.events import NewRequest, subscriber
from pyramid.httpexceptions import exception_response
from pyramid.renderers import JSON, render, render_to_response
from pyramid.session import check_csrf_token
from pyramid.settings import asbool, aslist
from pyramid_beaker import session_factory_from_settings


def to_json(value):
    """ A json filter for jinja2 """
    return render('json', value)

json_renderer = JSON()  # pylint: disable=C0103
json_renderer.add_adapter(datetime.datetime, lambda obj, r:
                          1000 * calendar.timegm(obj.utctimetuple()))
json_renderer.add_adapter(datetime.date,
                          lambda obj, _: obj.isoformat())
json_renderer.add_adapter(defaultdict,
                          lambda obj, _: dict(object))


@subscriber(NewRequest)
def check_csrf(event):
    request = event.request
    if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
        check_csrf_token(event.request)


def _error(request, error, message='Unknown error', status_code=400):
    """
    Construct an error response

    Parameters
    ----------
    error : str
        Identifying error key
    message : str, optional
        Human-readable error message
    status_code : int, optional
        HTTP return code (default 500)

    """
    data = {
        'error': error,
        'msg': message,
    }
    request.response.status_code = status_code
    return render_to_response('json', data, request)


def _raise_error(request, error, message='Unknown error', status_code=400):
    """
    Raise an error response.

    Use this when you need to return an error to the client from inside of
    nested function calls.

    Parameters
    ----------
    error : str
        Identifying error key
    message : str, optional
        Human-readable error message
    status_code : int, optional
        HTTP return code (default 500)

    """
    err = exception_response(status_code, detail=message)
    err.error = error
    raise err


def _assets(request, key):
    filename = os.path.join(os.path.dirname(__file__), 'files.json')
    settings = request.registry.settings
    debug = asbool(settings.get('pike.debug', False))
    if debug or request.registry.assets is None:
        with open(filename, 'r') as ifile:
            request.registry.assets = json.load(ifile)
    prefix = request.registry.settings.get('pike.url_prefix', 'gen').strip('/')
    for filename in request.registry.assets.get(key, []):
        yield posixpath.join(prefix, filename)


def _constants(request):
    data = {}
    for k, v in request.registry.client_constants.iteritems():
        if callable(v):
            v = v(request)
        if v is not None:
            data[k] = v
    return data


def _auth_callback(userid, request):
    perms = []
    setting = request.registry.settings.get('auth.' + userid)
    if setting is not None:
        principals = aslist(setting)
    else:
        now = datetime.datetime.utcnow()
        permlist = request.db(UserPerm) \
            .filter(UserPerm.start < now, email=userid).all()
        principals = set()
        for perm in permlist:
            if now < perm.end:
                principals.update(perm.perms)
    perms.extend(principals)
    return perms


def includeme(config):
    """ Set up and configure the app """
    settings = config.get_settings()
    config.include('pyramid_beaker')
    config.include('pyramid_duh')
    config.include('stiny.route')
    config.add_renderer('json', json_renderer)

    # Jinja2 configuration
    settings['jinja2.filters'] = {
        'static_url': 'pyramid_jinja2.filters:static_url_filter',
        'json': to_json,
    }
    settings['jinja2.directories'] = ['stiny:templates']
    config.include('pyramid_jinja2')
    config.commit()

    # Beaker configuration
    settings.setdefault('session.type', 'cookie')
    settings.setdefault('session.httponly', 'true')
    config.set_session_factory(session_factory_from_settings(settings))

    # Special request methods
    config.add_request_method(_error, name='error')
    config.add_request_method(_raise_error, name='raise_error')
    config.add_request_method(_constants, name='client_constants')
    config.add_request_method(lambda r, *a, **k: r.route_url('root', *a, **k),
                              name='rooturl')
    config.add_request_method(lambda r, u: _auth_callback(u, r), name='user_principals')

    prefix = settings.get('pike.url_prefix', 'gen').strip('/')
    config.registry.client_constants = {
        'URL_PREFIX': '/' + prefix,
        'USER': lambda r: r.authenticated_userid,
        'GOOGLE_CLIENT_ID': settings.get('google.client_id'),
        'PERMISSIONS': lambda r: r.effective_principals,
    }

    config.registry.assets = None
    config.add_request_method(_assets, name='assets')
    debug = asbool(settings.get('pike.debug', False))
    cache_age = 0 if debug else 31556926
    config.add_static_view(name=prefix,
                           path='stiny:gen',
                           cache_max_age=cache_age)

    # Auth
    config.set_authorization_policy(ACLAuthorizationPolicy())
    config.set_authentication_policy(AuthTktAuthenticationPolicy(
        secret=settings['authtkt.secret'],
        cookie_name=settings.get('auth.cookie_name', 'auth_tkt'),
        secure=asbool(settings.get('auth.secure', False)),
        timeout=int(settings.get('auth.timeout', 60 * 60 * 24 * 30)),
        reissue_time=int(settings.get('auth.reissue_time', 60 * 60 * 24 * 15)),
        max_age=int(settings.get('auth.max_age', 60 * 60 * 24 * 30)),
        http_only=asbool(settings.get('auth.http_only', True)),
        hashalg='sha512',
        callback=_auth_callback,
    ))
    config.set_default_permission('default')

    # Database
    engine = Engine()
    access_key = settings.get('aws.access_key')
    if access_key is None:
        access_key = os.environ['STINY_AWS_ACCESS_KEY']
    secret_key = settings.get('aws.secret_key')
    if secret_key is None:
        secret_key = os.environ['STINY_AWS_SECRET_KEY']
    engine.connect_to_region('us-west-1', access_key=access_key,
                             secret_key=secret_key)
    engine.register(UserPerm)
    engine.create_schema()
    config.registry.engine = engine
    config.add_request_method(lambda r: r.registry.engine, 'db', reify=True)

    # Start the worker that interfaces with the relays
    from .worker import Worker
    worker = Worker(isolate=asbool(settings.get('pi.debug', False)))
    worker.daemon = True
    worker.start()
    config.registry.worker = worker
    config.add_request_method(lambda r: r.registry.worker, name='worker',
                              reify=True)

    config.scan()


def main(config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('stiny')
    return config.make_wsgi_app()
