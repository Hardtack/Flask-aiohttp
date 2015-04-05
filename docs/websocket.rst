WebSocket
=========

Flask-aiohttp injects :class:`~aiohttp.web.WebSocketResponse` into your WSGI
environ, and provides api to use it.

This is not elegant solution for using websocket. But, it would be best
solution for now.

::

    from flask.ext.aiohttp import websocket


    @app.route('/echo')
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


You also can use most features of flask with websocket. ::

    from flask.ext.aiohttp import websocket


    @app.route('/hello/<name>')
    @websocket
    def hello(name):
        while True:
            msg = yield from aio.ws.receive_msg()

            if msg.tp == aiohttp.MsgType.text:
                aio.ws.send_str('Hello, {}'.format(name))
            elif msg.tp == aiohttp.MsgType.close:
                print('websocket connection closed')
                break
            elif msg.tp == aiohttp.MsgType.error:
                print('ws connection closed with exception %s',
                      aio.ws.exception())
                break
