""" Route configuration. """
from pyramid.security import Allow, Authenticated, DENY_ALL, ALL_PERMISSIONS


class Root(object):

    """
    Root context.

    Defines ACL, not much else.

    """
    __acl__ = [
        [Allow, 'admin', ALL_PERMISSIONS],
        [Allow, 'unlock', 'unlock'],
        [Allow, Authenticated, 'default'],
        DENY_ALL,
    ]

    def __init__(self, request):
        self.request = request


def includeme(config):
    """ Add the url routes """
    config.set_root_factory(Root)
    config.add_route('root', '/')

    config.add_route('logout', '/api/logout')
    config.add_route('login', '/api/login', request_method='POST')

    config.add_route('doorbell', '/api/home/doorbell')
    config.add_route('unlock', '/api/home/unlock')

    config.add_route('on_sms', '/api/home/sms')
