""" Stiny - A home automation assistant """
import os
import posixpath

import calendar
import datetime
import json
import logging
import requests
from collections import defaultdict
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.httpexceptions import exception_response
from pyramid.renderers import JSON, render, render_to_response
from pyramid.settings import asbool, aslist
from pyramid_beaker import session_factory_from_settings
from twilio.util import RequestValidator

from .gutil import Calendar, normalize_email


LOG = logging.getLogger(__name__)


def to_json(value):
    """ A json filter for jinja2 """
    return render('json', value)

json_renderer = JSON()  # pylint: disable=C0103
json_renderer.add_adapter(datetime.datetime, lambda obj, r:
                          1000 * calendar.timegm(obj.utctimetuple()))
json_renderer.add_adapter(datetime.date,
                          lambda obj, _: obj.isoformat())
json_renderer.add_adapter(defaultdict,
                          lambda obj, _: dict(obj))
json_renderer.add_adapter(Exception,
                          lambda e, _: str(e))


def _error(request, error, message='Unknown error', status_code=500):
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
    LOG.error("%s: %s", error, message)
    request.response.status_code = status_code
    return render_to_response('json', data, request, response=request.response)


def _raise_error(request, error, message='Unknown error', status_code=500):
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


def _auth_callback(userid, request):
    """ Get permissions for a user with an email. """
    n_userid = normalize_email(userid)
    perms = []
    # If permissions are declared in the config.ini file, just use those.
    setting = request.registry.settings.get('auth.' + n_userid)
    if setting is not None:
        principals = aslist(setting)
    else:
        principals = []
        if request.cal.is_guest(n_userid):
            principals.append('unlock')

    perms.extend(principals)
    return perms


def _validate_twilio(request):
    signature = request.headers.get('X-Twilio-Signature')
    if signature is None:
        return False
    validator = request.registry.twilio_validator
    return validator.validate(request.url, {}, signature)


def _call_worker(request, worker, command, **kwargs):
    host = request.registry.settings['worker.' + worker]
    fullpath = host + '/do/' + command
    headers = {'content-type': 'application/json'}
    response = requests.post(fullpath, data=json.dumps(kwargs),
                             headers=headers)
    response.raise_for_status()
    return response.json()


def includeme(config):
    """ Set up and configure the app """
    settings = config.get_settings()
    config.include('pyramid_beaker')
    config.include('pyramid_duh')
    config.include('pyramid_webpack')
    config.include('stiny.route')
    config.add_renderer('json', json_renderer)

    # Jinja2 configuration
    settings['jinja2.filters'] = {
        'static_url': 'pyramid_jinja2.filters:static_url_filter',
        'json': to_json,
    }
    settings['jinja2.directories'] = ['stiny:templates']
    settings['jinja2.extensions'] = ['pyramid_webpack.jinja2ext:WebpackExtension']
    config.include('pyramid_jinja2')
    config.commit()

    # Beaker configuration
    settings.setdefault('session.type', 'cookie')
    settings.setdefault('session.httponly', 'true')
    config.set_session_factory(session_factory_from_settings(settings))
    config.set_default_csrf_options(require_csrf=True, token=None)

    # Set admins from environment variable for local development
    if 'STINY_ADMINS' in os.environ:
        for email in aslist(os.environ['STINY_ADMINS']):
            email = normalize_email(email)
            settings['auth.' + email] = 'admin'

    # Set guests from environment variable for local development
    if 'STINY_GUESTS' in os.environ:
        for email in aslist(os.environ['STINY_GUESTS']):
            email = normalize_email(email)
            settings['auth.' + email] = 'unlock'

    # Special request methods
    config.add_request_method(_error, name='error')
    config.add_request_method(_raise_error, name='raise_error')
    config.add_request_method(lambda r, *a, **k: r.route_url('root', *a, **k),
                              name='rooturl')
    config.add_request_method(lambda r, u: _auth_callback(u, r),
                              name='user_principals')
    config.add_request_method(lambda r: r.registry.settings.get('google.client_id'),
                              name='google_client_id', reify=True)

    config.registry.phone_access = aslist(settings.get('phone_access', []))

    config.add_static_view(name='static', path='stiny:static',
                           cache_max_age=10 * 365 * 24 * 60 * 60)

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

    # Calendar
    config.registry.GOOGLE_WEB_CLIENT_ID = settings.setdefault(
        'google.client_id',
        os.environ.get('STINY_DEV_CLIENT_GOOGLE_CLIENT_ID'))
    server_client_id = settings.get('google.server_client_id')
    if server_client_id is None:
        server_client_id = os.environ['STINY_SERVER_GOOGLE_CLIENT_ID']
    config.registry.GOOGLE_CLIENT_ID = server_client_id
    client_secret = settings.get('google.server_client_secret')
    if client_secret is None:
        client_secret = os.environ['STINY_SERVER_GOOGLE_CLIENT_SECRET']
    cal_id = settings.get('google.calendar_id')
    if cal_id is None:
        cal_id = os.environ['STINY_CAL_ID']
    cal = Calendar(server_client_id, client_secret, calendar_id=cal_id)
    config.registry.calendar = cal
    config.add_request_method(lambda r: r.registry.calendar, 'cal', reify=True)

    twilio_token = settings.get('twilio.auth_token')
    if twilio_token is None:
        twilio_token = os.environ['STINY_TWILIO_AUTH_TOKEN']
    config.registry.twilio_validator = RequestValidator(twilio_token)
    config.add_request_method(_validate_twilio, name='validate_twilio')

    config.add_request_method(_call_worker, name='call_worker')

    config.scan()


def main(config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('stiny')
    return config.make_wsgi_app()
