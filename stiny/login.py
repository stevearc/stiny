""" Views for logging in """
import requests
from pyramid.security import forget, remember, NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid_duh import argify
from oauth2client import client, crypt


@view_config(route_name='logout')
def logout(request):
    """ Remove stored user credentials from cookies. """
    request.response.headers.extend(forget(request))
    return request.response


@view_config(
    route_name='login',
    permission=NO_PERMISSION_REQUIRED,
    renderer='json')
@argify
def login(request, access_token):
    """
    Validate a google access token and retrieve user's email.

    Returns
    -------
    user : str
        User email.
    permissions : list
        List of permissions that the user has.

    """
    try:
        idinfo = client.verify_id_token(access_token,
                                        request.registry.GOOGLE_WEB_CLIENT_ID)
        if idinfo['aud'] not in [request.registry.GOOGLE_WEB_CLIENT_ID]:
            raise crypt.AppIdentityError("Unrecognized client.")
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise crypt.AppIdentityError("Wrong issuer.")
    except crypt.AppIdentityError as e:
        return request.error('token', e.message, 400)

    email = idinfo.get('email')
    if email is None:
        return request.error('google_data', "Could not find Google email")

    request.response.headers.extend(remember(request, email))
    return {
        'user': email,
        'permissions': request.user_principals(email),
    }
