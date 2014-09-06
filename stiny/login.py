""" Views for logging in """
import velruse
from pyramid.httpexceptions import HTTPFound, HTTPForbidden
from pyramid.security import forget, remember, NO_PERMISSION_REQUIRED
from pyramid.settings import aslist, asbool
from pyramid.view import view_config
from passlib.apps import custom_app_context as pwd_context
from pyramid_duh import argify


@view_config(route_name='logout')
def logout(request):
    response = HTTPFound(location=request.route_url('root'))
    response.headers.extend(forget(request))
    return response

@view_config(context=HTTPForbidden, permission=NO_PERMISSION_REQUIRED, renderer='login.jinja2')
def login(context, request):
    secure = asbool(request.registry.settings.get('session.secure', False))
    request.response.set_cookie('CSRF-Token', request.session.get_csrf_token(),
                                secure=secure)
    return {
        'next': request.path,
    }

@view_config(route_name='do_login', permission=NO_PERMISSION_REQUIRED, renderer='json')
@argify
def do_login(request, username, password):
    db_pass = request.registry.settings.get('auth.%s' % username)
    if db_pass is None:
        return {
            'error': 'Invalid username'
        }
    if not pwd_context.verify(password, db_pass):
        return {
            'error': 'Invalid password'
        }
    request.response.headers.extend(remember(request, username))
    return {}


# @view_config(route_name='login', permission=NO_PERMISSION_REQUIRED)
# @view_config(context=HTTPForbidden, permission=NO_PERMISSION_REQUIRED)
# @argify
# def do_login(request, next=None):
#     """ Store the redirect in the session and log in with google """
#     if request.authenticated_userid is not None:
#         return request.error(403, "Forbidden", 403)
#     request.session['next'] = next
#     return HTTPFound(location=velruse.login_url(request, 'google'))


# @view_config(context='velruse.AuthenticationComplete', permission=NO_PERMISSION_REQUIRED)
# def on_login(context, request):
#     """ Called when a user successfully logs in """
#     email = context.profile['verifiedEmail'].lower()
#     request.response.headers.extend(remember(request, email))
#     next_url = request.rooturl()
#     next_hash = request.session.pop('next', None)
#     if next_hash is not None:
#         next_url += '#!' + next_hash
#     return HTTPFound(location=next_url, headers=request.response.headers)


# @view_config(context='velruse.AuthenticationDenied', permission=NO_PERMISSION_REQUIRED)
# def on_login_denied(request):
#     """ Called when the login is denied """
#     anchor = "!/login?next=%s" % (request.session.get('next') or '/')
#     url = request.rooturl(_anchor=anchor)
#     return HTTPFound(location=url)
