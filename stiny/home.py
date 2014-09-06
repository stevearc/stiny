from pyramid.view import view_config


@view_config(route_name='unlock', request_method='POST', permission='lock')
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
