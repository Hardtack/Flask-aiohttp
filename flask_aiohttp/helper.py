""":mod:`helper` --- Helpers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides various utilities.

"""
import asyncio
import functools

from flask import current_app, request, abort

from .util import async_response


__all__ = ['async', 'websocket', 'has_websocket', 'wrap_wsgi_middleware']


def async(fn):
    """Decorate flask's view function for asyncio.

    ::

        @async
        def foo():
            yield from asyncio.sleep(3)
            return 'foo'


    :param fn: Function to be decorated.

    :returns: decorator.

    """
    fn = asyncio.coroutine(fn)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        coroutine = functools.partial(fn, *args, **kwargs)
        return async_response(coroutine(), current_app, request)
    return wrapper


def websocket(fn=None, *, failure_status_code: int=400):
    """Decorate flask's view function for websocket

    :param failure_status_code: status code for failure

    ::

        @async
        def foo():
            data = yield from aio.ws.receive()
            ...

    Or ::

        @async(failure_status_code=404)
        def bar():
            data = yield from aio.ws.receive()
            ...

    """
    if fn is not None:
        # For simple `@async` call
        return websocket(failure_status_code=400)(fn)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not has_websocket():
                # Accept only websocket request
                abort(failure_status_code)
            else:
                yield from func(*args, **kwargs)
                return 'Done', 200
        return async(wrapper)
    return decorator


def has_websocket() -> bool:
    """Does current request contains websocket?"""
    return request.environ.get('wsgi.websocket', None) is not None


def wrap_wsgi_middleware(middleware, *args):
    """Wrap plain WSGI middleware to working asynchronously.

    Most WSGI middlewares called like following break our coroutine call ::

        flask.wsgi_app = middleware(wsgi_app)

    So we can prevent breaking coroutine by this wrapper ::

        flask.wsgi_app = wrap_wsgi_middleware(middleware)(wsgi_app)

    Like most of asyncio functions, you have to

    :param middleware: WSGI middleware to be wrapped
    :return: wrapped middleware

    """
    def wrapper(wsgi):
        _signal = object()

        # Wrap the coroutine WSGI app
        @functools.wraps(wsgi)
        def wsgi_wrapper(environ, start_response):
            rv = yield from wsgi(environ, start_response)
            # Yield signal for end original yield
            yield _signal
            yield rv

        # Create concrete middleware
        concrete_middleware = middleware(wsgi_wrapper, *args)

        # Wrap the middleware again
        @functools.wraps(concrete_middleware)
        @asyncio.coroutine
        def wrapped(environ, start_response):
            iterator = iter(concrete_middleware(environ, start_response))
            while True:
                item = next(iterator)
                if item is not _signal:
                    yield item
                else:
                    break
            # Now, original yielding ended. next yielded value is return
            # value of coroutine.
            rv = next(iterator)
            return rv
        return wrapped
    return wrapper
