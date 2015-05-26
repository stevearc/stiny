""" API endpoints related to home operations. """
import logging

from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config

LOG = logging.getLogger(__name__)


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


@view_config(route_name='on_sms', request_method='GET', renderer='string',
             permission=NO_PERMISSION_REQUIRED)
def received_sms(request):
    if not request.validate_twilio():
        return request.error('auth', "Failed HMAC")
    from_number = request.param('From')
    if not request.cal.is_guest(from_number) and \
            from_number not in request.registry.phone_access:
        LOG.warning("%r attempted unauthorized entry", from_number)
        return ("I'm sorry, you are not authorized to enter this dwelling. "
                "Please contact the residents.")
    request.call_worker('door', 'on_off', relay='outside_latch', duration=3)
    return request.response
