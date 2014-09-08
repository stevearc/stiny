""" Views for logging in """
import requests
from pyramid.security import forget, remember, NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid_duh import argify


@view_config(route_name='logout')
def logout(request):
    request.response.headers.extend(forget(request))
    return request.response


@view_config(
    route_name='login',
    permission=NO_PERMISSION_REQUIRED,
    renderer='json')
@argify
def login(request, access_token):

    resp = requests.get('https://www.googleapis.com/plus/v1/people/me',
                        params={'access_token': access_token})
    if not resp.ok:
        return request.error(
            'google_api',
            "Could not retrieve email from Google")

    data = resp.json()

    email = None
    for addr in data['emails']:
        if addr['type'] == 'account':
            email = addr['value']

    if email is None:
        return request.error('google_data', "Could not find Google email")

    request.response.headers.extend(remember(request, email))
    return {
        'user': email,
        'permissions': request.user_principals(email),
    }
