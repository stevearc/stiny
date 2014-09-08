""" General views """
import logging
import traceback
from pyramid.httpexceptions import HTTPException, HTTPServerError, HTTPNotFound
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.settings import asbool
from pyramid.view import view_config


LOG = logging.getLogger(__name__)


@view_config(
    route_name='root',
    permission=NO_PERMISSION_REQUIRED,
    renderer='index.jinja2')
def index_view(request):
    """ Root view (/) """
    secure = asbool(request.registry.settings.get('session.secure', False))
    request.response.set_cookie('CSRF-Token', request.session.get_csrf_token(),
                                secure=secure)
    prefix = request.registry.settings.get('pike.url_prefix', 'gen').strip('/')
    return {
        'prefix': '/' + prefix,
    }


@view_config(context=HTTPNotFound, permission=NO_PERMISSION_REQUIRED)
def handle_404(context, request):
    return context


@view_config(
    context=Exception,
    renderer='json',
    permission=NO_PERMISSION_REQUIRED)
@view_config(
    context=HTTPException,
    renderer='json',
    permission=NO_PERMISSION_REQUIRED)
def format_exception(context, request):
    """
    Catch all app exceptions and render them nicely

    This will keep the status code, but will always return parseable json

    Returns
    -------
    error : str
        Identifying error key
    msg : str
        Human-readable error message
    stacktrace : str, optional
        If pyramid.debug = true, also return the stacktrace to the client

    """
    LOG.exception(context.message)
    if not request.path.startswith('/api/'):
        if isinstance(context, HTTPException):
            return context
        else:
            return HTTPServerError(context.message)
    error = {
        'error': getattr(context, 'error', 'unknown'),
        'msg': context.message,
    }
    if asbool(request.registry.settings.get('pyramid.debug', False)):
        error['stacktrace'] = traceback.format_exc()
    request.response.status_code = getattr(context, 'status_code', 500)
    if (request.response.status_code == 403 and
            request.authenticated_userid is None):
        request.response.status_code = 401
    return error
