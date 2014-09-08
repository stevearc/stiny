""" API endpoints related to home operations. """
from datetime import datetime
from flywheel import ConditionalCheckFailedException
from pyramid.view import view_config
from pyramid_duh import argify

from .models import UserPerm, State


@view_config(route_name='unlock', request_method='POST', permission='unlock')
def unlock(request):
    """ Unlock the gate for a brief period """
    request.worker.do('on_off', relay='outside_latch', duration=3)
    return request.response


@view_config(route_name='doorbell', request_method='POST', permission='troll')
def ring_doorbell(request):
    """ Ring the doorbell """
    request.worker.do('on_off', relay='doorbell', duration=0.2)
    return request.response


@view_config(route_name='perm_schedule', request_method='GET',
             permission='admin', renderer='json')
def perm_schedule(request):
    """ Get all scheduled guest permissions. """
    perms = request.db.scan(UserPerm).all()
    perms.sort(key=lambda p: p.start)
    return {
        'perms': perms
    }


@view_config(route_name='perm_schedule', request_method='POST',
             permission='admin', renderer='json')
@argify(perms=set, start=datetime, end=datetime)
def add_perm_schedule(request, email, perms, start, end):
    """ Schedule a permission grant for a user. """
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
    """ Remove a permission grant for a user. """
    request.db(UserPerm).filter(email=email, start=start).delete()
    return {}


@view_config(route_name='party_schedule', request_method='GET',
             permission='admin', renderer='json')
def party_schedule(request):
    """ Get all scheduled parties. """
    parties = request.db.scan(State).filter(name='party').all()
    parties.sort(key=lambda p: p.start)
    return {
        'schedule': parties
    }


@view_config(route_name='party_schedule', request_method='POST',
             permission='admin', renderer='json')
@argify(start=datetime, end=datetime)
def add_party_schedule(request, start, end):
    """ Schedule a perty. """
    party = State('party', start, end)
    try:
        request.db.save(party, overwrite=False)
    except ConditionalCheckFailedException:
        return request.error('dupe', "Party already scheduled for that time")
    return {
        'party': party
    }


@view_config(route_name='party_schedule_del', request_method='POST',
             permission='admin', renderer='json')
@argify(start=datetime)
def delete_party_schedule(request, start):
    """ Delete a scheduled party. """
    request.db(State).filter(name='party', start=start).delete()
    return {}
