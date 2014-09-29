""" API endpoints related to home operations. """
from pyramid.view import view_config


@view_config(route_name='unlock', request_method='POST', permission='unlock')
def unlock(request):
    """ Unlock the gate for a brief period """
    request.call_worker('door', 'on_off', relay='outside_latch', duration=3)
    return request.response


@view_config(route_name='doorbell', request_method='POST', permission='troll')
def ring_doorbell(request):
    """ Ring the doorbell """
    request.call_worker('door', 'on_off', relay='doorbell', duration=0.2)
    return request.response
