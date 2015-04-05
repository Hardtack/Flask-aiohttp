import abc
import asyncio
import itertools

import aiohttp.web
from aiohttp.wsgi import WSGIServerHttpProtocol

from .util import is_websocket_request


class WSGIHandlerBase(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def handle_request(self, request: aiohttp.web.Request):
        pass

    @asyncio.coroutine
    def __call__(self, request: aiohttp.web.Request):
        response = yield from self.handle_request(request)
        return response


class WSGIWebSocketHandler(WSGIHandlerBase):
    """WSGI request handler for aiohttp web application."""

    def __init__(self, wsgi):
        self.wsgi = wsgi

    @asyncio.coroutine
    def handle_request(self, request: aiohttp.web.Request) -> \
            aiohttp.web.StreamResponse:
        """Handle WSGI request with aiohttp"""

        # Use aiohttp's WSGI implementation
        protocol = WSGIServerHttpProtocol(request.app, True)
        protocol.transport = request.transport

        # Build WSGI Response
        environ = protocol.create_wsgi_environ(request, request.content)

        # Create responses
        ws = aiohttp.web.WebSocketResponse()
        response = aiohttp.web.StreamResponse()

        #: Write delegate
        @asyncio.coroutine
        def write(data):
            yield from response.write(data)

        #: EOF Write delegate
        @asyncio.coroutine
        def write_eof():
            yield from response.write_eof()

        # WSGI start_response function
        def start_response(status, headers, exc_info=None):
            if exc_info:
                raise exc_info[1]

            status_parts = status.split(' ', 1)
            status = int(status_parts.pop(0))
            reason = status_parts[0] if status_parts else None

            response.set_status(status, reason=reason)

            for name, value in headers:
                response.headers[name] = value

            response.start(request)

            return write
        if is_websocket_request(request):
            ws.start(request)

            # WSGI HTTP responses in websocket are meaningless.
            def start_response(status, headers, exc_info=None):
                if exc_info:
                    raise exc_info[1]
                ws.start(request)
                return []

            @asyncio.coroutine
            def write(data):
                return

            @asyncio.coroutine
            def write_eof():
                return

            response = ws
        else:
            ws = None

        # Add websocket response to WSGI environment
        environ['wsgi.websocket'] = ws

        # Run WSGI app
        response_iter = self.wsgi(environ, start_response)

        try:
            iterator = iter(response_iter)

            wsgi_response = []
            try:
                item = next(iterator)
            except StopIteration as stop:
                try:
                    iterator = iter(stop.value)
                except TypeError:
                    pass
                else:
                    wsgi_response = iterator
            else:
                if isinstance(item, bytes):
                    # This is plain WSGI response iterator
                    wsgi_response = itertools.chain([item], iterator)
                else:
                    # This is coroutine
                    yield item
                    wsgi_response = yield from iterator
            for item in wsgi_response:
                yield from write(item)

            yield from write_eof()
        finally:
            if hasattr(response_iter, 'close'):
                response_iter.close()

        # Return selected response
        return response
