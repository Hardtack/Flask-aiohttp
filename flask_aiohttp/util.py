import asyncio

import flask
import aiohttp.web
from aiohttp import hdrs
from flask.ctx import RequestContext
from werkzeug.local import LocalProxy


def is_websocket_request(request: aiohttp.web.Request) -> bool:
    """Is the request websocket request?

    :param request: aiohttp web request object

    """
    upgrade = request.headers.get(hdrs.UPGRADE, '').lower().strip()
    connection = request.headers.get(hdrs.CONNECTION, '').lower()
    return 'websocket' == upgrade and 'upgrade' in connection


def freeze(object_or_proxy):
    """Get current object of `object_or_proxy` if it is LocalProxy"""
    if isinstance(object_or_proxy, LocalProxy):
        return object_or_proxy._get_current_object()
    return object_or_proxy


def async_response(coroutine,
                   app: flask.Flask or LocalProxy,
                   request: flask.Request or LocalProxy) -> \
        flask.Response:
    """Convert coroutine to asynchronous flask response.

    :param coroutine: coroutine
    :param app: Flask application
    :param request: Current request
    :returns: asynchronous Flask response

    """

    #: :type: flask.Flask
    app = freeze(app)

    # :type: flask.Request
    request = freeze(request)

    class AsyncResponse(app.response_class):
        def __init__(self):
            super().__init__(coroutine)

        @asyncio.coroutine
        def call_response(self):
            rv = app.preprocess_request()
            if rv is None:
                try:
                    rv = yield from self.response
                except Exception as e:
                    rv = app.handle_user_exception(e)
            if asyncio.iscoroutine(rv):
                rv = yield from rv
            response = app.make_response(rv)
            response = app.process_response(response)
            return response

        @asyncio.coroutine
        def __call__(self, environ, start_response):
            with RequestContext(app, environ, request):
                try:
                    # Fetch data from coroutine
                    rv = yield from self.call_response()
                except Exception as e:
                    rv = app.handle_exception(e)
                    if asyncio.iscoroutine(rv):
                        rv = yield from rv
                    rv = app.make_response(rv)
                if asyncio.iscoroutine(rv):
                    rv = yield from rv

            # Call as WSGI app
            if isinstance(rv, app.response_class):
                return rv(environ, start_response)

            status = self.status
            headers = self.get_wsgi_headers(environ)
            app_iter = []

            start_response(status, headers)
            return app_iter

    return AsyncResponse()
