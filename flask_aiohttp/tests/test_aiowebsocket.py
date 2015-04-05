import time
import pytest
import asyncio
import threading
import contextlib
import urllib.parse
import urllib.request

import aiohttp
from flask import Flask, request
from websocket import WebSocket
from werkzeug.debug import DebuggedApplication

from .. import AioHTTP, wrap_wsgi_middleware, async, websocket


class Server(contextlib.ContextDecorator):
    def __init__(self, app: Flask, aio: AioHTTP, *,
                 host='127.0.0.1', port=0):
        super().__init__()
        self.app = app
        self.aio = aio
        self.host = host
        self.port = port
        self.loop = asyncio.get_event_loop()
        self._server = None
        self.condition = threading.Condition(threading.Lock())

    def start(self):
        # Wrap WSGI app with werkzeug debugger.
        self.app.wsgi_app = wrap_wsgi_middleware(DebuggedApplication)(
            self.app.wsgi_app)

        thread = threading.Thread(target=self.run)
        thread.start()

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        time.sleep(0.001)  # For bypassing unknown exception at stopping loop.
        self.stop()

    @property
    def server(self):
        with self.condition:
            if self._server is None:
                self.condition.wait()
        return self._server

    @server.setter
    def server(self, server):
        with self.condition:
            self._server = server
            if server is not None:
                self.condition.notify_all()

    def run(self):
        asyncio.set_event_loop(self.loop)

        # Create coroutine
        coroutine = self.loop.create_server(
            self.app.aiohttp_app.make_handler(), self.host, self.port)
        # Get server
        server = self.loop.run_until_complete(coroutine)
        self.server = server
        # Run until `stop()`
        self.loop.run_forever()

    @property
    def address(self):
        #: :type: socket.socket
        sock = self.server.sockets[0]
        return '{}:{}'.format(*sock.getsockname())

    @property
    def base_url(self):
        return 'http://' + self.address

    @property
    def ws_base_url(self):
        return 'ws://' + self.address

    def ws_url(self, path, **params):
        url = self.ws_base_url + path
        if params:
            url += '?' + urllib.parse.urlencode(params)
        return url

    def url(self, path, **params):
        url = self.base_url + path
        if params:
            url += '?' + urllib.parse.urlencode(params)
        return url

    def request(self, method, path, params=None):
        r = urllib.request.Request(self.url(path, **params),
                                   method=method.upper())
        with urllib.request.urlopen(r) as response:
            return response.readall().decode('utf-8')

    def get(self, path, **kwargs):
        return self.request('GET', path, params=kwargs)


@pytest.fixture
def app():
    app = Flask(__name__)
    return app


@pytest.fixture
def aio(app: Flask):
    return AioHTTP(app)


def test_flask(app: Flask, aio: AioHTTP):
    """Test for checking flask working find"""
    @app.route('/foo')
    def foo():
        return 'foo'

    @app.route('/bar')
    def bar():
        def stream():
            yield 'bar'
        return app.response_class(stream())

    with Server(app, aio) as server:
        assert 'foo' == server.get('/foo')
        assert 'bar' == server.get('/bar')


def test_async(app: Flask, aio: AioHTTP):
    """Test for asynchronous I/O in Flask view"""
    @app.route('/foo')
    def foo():
        return 'foo'

    @app.route('/lazy-foo')
    @async
    def lazy_foo():
        response = yield from aiohttp.request('GET', request.host_url + 'foo')
        data = yield from response.read()
        return data

    @app.route('/streaming-foo')
    @async
    def streaming_foo():
        response = yield from aiohttp.request('GET', request.host_url + 'foo')
        data = yield from response.read()

        def stream():
            yield data
        return app.response_class(stream())

    with Server(app, aio) as server:
        assert 'foo' == server.get('/foo')
        assert 'foo' == server.get('/lazy-foo')
        assert 'foo' == server.get('/streaming-foo')


def test_websocket(app: Flask, aio: AioHTTP):
    """Test for websocket"""
    @app.route('/echo')
    @websocket
    def echo():
        while True:
            msg = yield from aio.ws.receive_msg()

            if msg.tp == aiohttp.MsgType.text:
                aio.ws.send_str(msg.data)
            elif msg.tp == aiohttp.MsgType.close:
                break
            elif msg.tp == aiohttp.MsgType.error:
                break

    with Server(app, aio) as server:
        ws = WebSocket()
        ws.connect(server.ws_url('/echo'))
        try:
            ws.send('foo')
            assert 'foo' == ws.recv()
        finally:
            ws.close()


def test_request_hook(app: Flask, aio: AioHTTP):
    """Test for Flask request hook"""
    @app.before_request
    def before_request():
        request.foo = []
        request.foo.append('a')

    @app.after_request
    def after_request(response):
        request.foo.append('c')
        return response

    @app.teardown_request
    def teardown_request(exc):
        request.foo.append('d')

    @app.route('/hook')
    @async
    def hook():
        request.foo.append('b')

        return ''.join(request.foo)

    with Server(app, aio) as server:
        assert 'ab' == server.get('/hook')
