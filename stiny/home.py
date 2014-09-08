from datetime import datetime
from flywheel import ConditionalCheckFailedException
from pyramid.view import view_config
from pyramid_duh import argify

from .models import UserPerm


@view_config(route_name='unlock', request_method='POST', permission='unlock')
def unlock(request):
    request.worker.do('on_off', relay='outside_latch', duration=3)
    return request.response


@view_config(route_name='doorbell', request_method='POST', permission='troll')
def ring_doorbell(request):
    request.worker.do('on_off', relay='doorbell', duration=0.1)
    return request.response


@view_config(
    route_name='party_toggle',
    request_method='POST',
    renderer='json',
    permission='admin')
def party_toggle(request):
    mode = request.worker.party_mode
    request.worker.do('party_toggle')
    return {
        'party': not mode,
    }


@view_config(route_name='party', request_method='GET', renderer='json')
def party(request):
    mode = request.worker.party_mode
    return {
        'party': mode,
    }


@view_config(route_name='perm_schedule', request_method='GET',
             permission='admin', renderer='json')
def perm_schedule(request):
    perms = request.db.scan(UserPerm).all()
    perms.sort(key=lambda p: p.start)
    return {
        'perms': perms
    }


@view_config(route_name='perm_schedule', request_method='POST',
             permission='admin', renderer='json')
@argify(perms=set, start=datetime, end=datetime)
def add_perm_schedule(request, email, perms, start, end):
    perm = UserPerm(email, start, end, perms)
    try:
        request.db.save(perm, overwrite=False)
    except ConditionalCheckFailedException:
        return request.error('dupe', "User already scheduled for that time")
    return {
        'perm': perm
    }


@view_config(route_name='perm_schedule_del', request_method='POST',
             permission='admin', renderer='json')
@argify(start=datetime)
def delete_perm_schedule(request, email, start):
    request.db(UserPerm).filter(email=email, start=start).delete()
    return {}
