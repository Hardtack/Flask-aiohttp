Flask-aiohttp --- Asynchronous Flask using aiohttp.
===================================================

.. image:: http://unmaintained.tech/badge.svg
   :target: http://unmaintained.tech/
   :alt: No Maintenance Intended

**EXPERIMENTAL**
----------------

I made this project for testing compatability between WSGI & Async IO.

Since WSGI has no consideration of Async IO, Flask-aiohttp cannot be perfect.

So, I don't recommend you to use this library for production. Libraries that was made for Async IO would be better choice (Like gevent, Tornado or AioHTTP).


Features
--------

*   Coroutine view function

    You can make view function to asyncio coroutine using :func:`async`. ::

        @app.route('/slow')
        @async
        def slow():
            yield from asyncio.sleep(3)
            return 'sorry!'

*   Asynchronous I/O in view function

    You can do asynchronous I/O in your view function. ::

        @app.route('/zuck')
        @async
        def zuck():
            response = yield from aiohttp.request(
                'GET', 'https://graph.facebook.com/zuck')
            data = yield from response.read()
            return data

*   Websocket

    You can use aiohttp's WebSocketResponse in your Flask view function. ::

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

*   Flask URL routing

    It surely compatible with flask's view routing. ::

        @app.route('/param/<arg>')
        @websocket
        def param(arg):
            while True:
                msg = yield from aio.ws.receive_msg()

                if msg.tp == aiohttp.MsgType.text:
                    aio.ws.send_str(arg)
                elif msg.tp == aiohttp.MsgType.close:
                    print('websocket connection closed')
                    break
                elif msg.tp == aiohttp.MsgType.error:
                    print('ws connection closed with exception %s',
                          aio.ws.exception())
                    break

Usage
-----

You can use it just like plain Flask extensions. ::

    import flask
    from flask.ext.aiohttp import AioHTTP

    app = flask.Flask(__name__)
    aio = AioHTTP(app)

or ::

    aio = AioHTTP()
    aio.init_app(app)

But, you have to run the application using our runner to be run asynchronously.
::

    if __name__ == '__main__':
        aio.run(app, debug=True)

Documentation
-------------

`Read the docs<http://flask-aiohttp.readthedocs.org/>`
