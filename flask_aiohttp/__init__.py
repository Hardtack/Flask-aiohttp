""":mod:`flask_aiohttp` --- Asynchronous Flask with aiohttp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides Flask extension for asynchronous I/O.

With this extension, we can use `asyncio.coroutine` as Flask's view function.
So, we can add
asyncio-redis <https://github.com/jonathanslenders/asyncio-redis>`_, or
websocket support to your application.

To make view asynchronous, just simply add :func:`helper.async` decorator to
your view function ::

    @app.route('/foo')
    @async
    def lazy():
        yield from asyncio.sleep(3)
        return 'Done'

You have to run your flask application with :class:`AioHTTP` ::

    aio = AioHTTP(app)

    aio.run(app)

And you can also use gunicorn ::

    aio = AioHTTP(flask_app)

    app = aio.create_aiohttp_app(flask_app)

    # Run gunicorn by
    #
    # gunicorn your_module:app -k aiohttp.worker.GunicornWebWorker
    # -b localhost:8080

You can even use aiohttp's websocket in your Flask application using
:func:`helper.websocket` ::

    aio = AioHTTP(flask_app)

    @app.route('echo')
    @websocket
    def echo():
        while True:
            msg = yield from aio.ws.receive_msg()

            if msg.tp == aiohttp.MsgType.text:
                aio.ws.send_str(msg.data)
            elif msg.tp == aiohttp.MsgType.close:
                print('websocket connection closed')
                break
            elif msg.tp == aiohttp.MsgType.error:
                print('ws connection closed with exception %s',
                      aio.ws.exception())
                break

"""
import os
import asyncio
import logging

import flask
import aiohttp.web
from flask import request
from werkzeug.debug import DebuggedApplication
from werkzeug.serving import run_with_reloader

from .helper import async, websocket, has_websocket, wrap_wsgi_middleware
from .handler import WSGIHandlerBase, WSGIWebSocketHandler


__all__ = ['AioHTTP', 'async', 'websocket', 'has_websocket',
           'wrap_wsgi_middleware']


class AioHTTP(object):
    """Flask middleware for aiohttp"""

    def __init__(self, app: flask.Flask=None, *,
                 handler_factory=WSGIWebSocketHandler):
        """

        :param app:
            Flask application

        :param handler_factory:
            aiohttp request handler factory. Factory should accept a single
            flask application.

        """
        self.handler_factory = handler_factory
        if app is not None:
            self.init_app(app)

    def init_app(self, app: flask.Flask):
        """Init Flask app

        :param app: Flask application

        """
        app.aiohttp_app = self.create_aiohttp_app(app)

    def create_aiohttp_app(self, app: flask.Flask) -> aiohttp.web.Application:
        """Create aiohttp web application from Flask application

        :param app: Flask application
        :returns: aiohttp web application

        """
        # aiohttp web application instance
        aio_app = aiohttp.web.Application()

        # WSGI handler for aiohttp
        wsgi_handler = self.handler_factory(app)

        # aiohttp's router should accept any possible HTTP method of request.
        aio_app.router.add_route('*', r'/{path:.*}', wsgi_handler)
        return aio_app

    @staticmethod
    def run(app: flask.Flask, *,
            host='127.0.0.1', port=None, debug=False, loop=None):
        """Run Flask application on aiohttp

        :param app: Flask application
        :param host: host name or ip
        :param port: port (default is 5000)
        :param debug: debug?

        """
        # Check initialization status of flask app.
        if getattr(app, 'aiohttp_app', None) is None:
            raise RuntimeError(
                "This application is not initialized for Flask-aiohttp. "
                "Please initialize the app by `aio.init_app(app)`.")

        # Configure args
        if port is None:
            server_name = app.config['SERVER_NAME']
            if server_name and ':' in server_name:
                port = int(server_name.rsplit(':', 1)[-1])
            else:
                port = 5000
        loop = loop or asyncio.get_event_loop()

        # Define run_server
        def run_server():
            # run_server can be called in another thread
            asyncio.set_event_loop(loop)
            coroutine = loop.create_server(
                app.aiohttp_app.make_handler(), host, port)
            loop.run_until_complete(coroutine)
            try:
                loop.run_forever()
            except KeyboardInterrupt:
                pass

        # Configure logging
        file_handler = logging.StreamHandler()
        app.logger.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        if debug:
            # Logging
            app.logger.setLevel(logging.DEBUG)

            # Wrap WSGI app with werkzeug debugger.
            app.wsgi_app = wrap_wsgi_middleware(DebuggedApplication)(
                app.wsgi_app)

            if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
                app.logger.info(' * Running on http://{}:{}/'
                                .format(host, port))

            # Run with reloader
            run_with_reloader(run_server)
        else:
            app.logger.info(' * Running on http://{}:{}/'.format(host, port))
            run_server()

    @property
    def ws(self) -> aiohttp.web.WebSocketResponse:
        """Websocket response of aiohttp"""

        ws = request.environ.get('wsgi.websocket', None)
        if ws is None:
            raise RuntimeError('Request context is not a WebSocket context.')
        return ws
