import json
import asyncio

import aiohttp
from flask import Flask, current_app

from flask_aiohttp import AioHTTP
from flask_aiohttp.helper import async, websocket

app = Flask(__name__)

aio = AioHTTP(app)


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


@app.route('/api')
@async
def api():
    response = yield from aiohttp.request(
        'GET', 'https://graph.facebook.com/zuck')
    data = yield from response.read()
    return data


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


@app.route('/late')
@async
def late():
    yield from asyncio.sleep(3)

    data = {
        'data': 'done'
    }

    data = json.dumps(data)
    current_app.response_class(data, headers={
        'Content-Type': 'application/json',
    }, status=201)
    return 'done'


@app.route('/plain')
def plain():
    return 'Hello, World!'


@app.route('/stream')
def stream():
    def f():
        yield 'Hello, '
        yield 'World!'
    return app.response_class(f())


@app.route('/async-stream')
@async
def async_stream():
    def f():
        yield 'I\'m '
        yield 'sorry!'
    yield from asyncio.sleep(1)
    return app.response_class(f())


def main():
    aio.run(app, debug=True)

if __name__ == '__main__':
    main()
