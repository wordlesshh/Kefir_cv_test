from functools import wraps
from inspect import isawaitable

from sanic import exceptions


def request_validation(pagination=False, check_token=False, check_pk=False):
    def decorator(fn):
        @wraps(fn)
        async def inner(request, *args, **kwargs):
            if pagination:
                try:
                    page = int(request.headers.get('Page', None))
                    size = int(request.headers.get('Size', None))
                except ValueError:
                    raise exceptions.SanicException("Validation Error", status_code=422)
                if not page or not size:
                    raise exceptions.InvalidUsage('Bad Request')
                if page < 1 or size < 1:
                    raise exceptions.SanicException("Validation Error", status_code=422)

            if check_token:
                token = request.cookies.get("token")
                if not token:
                    raise exceptions.Unauthorized("Response 401 Current User Users Current Get")

            if check_pk:
                try:
                    pk = int(request.match_info['pk'])
                except ValueError:
                    raise exceptions.SanicException("Validation Error", status_code=422)

            retval = fn(request, *args, **kwargs)
            if isawaitable(retval):
                retval = await retval
            return retval
        return inner
    return decorator
