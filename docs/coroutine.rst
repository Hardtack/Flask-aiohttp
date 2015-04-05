Coroutine
=========

You can use asyncio's coroutine [#]_ in flask's view function using this
extension. ::

    from flask.ext.aiohttp import async

    @app.route('/late-response')
    @async  # It marks view function as asyncio coroutine
    def late_response():
        yield from asyncio.sleep(3)
        return "Sorry, I'm late!"


So, you can use aiohttp's request modules in flask. ::

    from flask.ext.aiohttp import async

    @app.route('/zuck')
    @async
    def zuck():
        response = yield from aiohttp.request(
            'GET', 'https://graph.facebook.com/zuck')
        data = yield from response.read()

        return data

And you can surely use flask's common feature. ::

    import json
    import urllib.parse

    from flask import current_app, request
    from flask.ext.aiohttp import async

    @app.route('/fb/<name>')
    @async
    def facebook_profile(name):
        if request.args.get('secure', False):
            url = 'https://graph.facebook.com/'
        else:
            url = 'http://graph.facebook.com/'
        url = url + urllib.parse.quote(name)
        response = yield from aiohttp.request('GET', url)
        data = yield from response.read()
        data = json.loads(data)

        def stream():
            if request.args.get('wrap', False):
                data = {
                    'data': data
                }
            yield json.dumps(data)
        return current_app.response_class(stream())


.. note::

    Since coroutine implemented by using streaming response, you have to be
    care about using request hook.

    :func:`~flask.app.Flask.before_request`,
    :func:`~flask.app.Flask.after_request`,
    :func:`~flask.app.Flask.teardown_request` will be called twice.

    Each asynchronous request's functions will be called in following sequence.

    1.  :func:`~flask.app.Flask.before_request`
    2.  **Flask-aiohttp's** streaming response containing coroutine
    3.  :func:`~flask.app.Flask.after_request`
    4.  :func:`~flask.app.Flask.teardown_request`

    *Streaming response starts here*

    5.  :func:`~flask.app.Flask.before_request`
    6.  Your coroutine response
    7.  :func:`~flask.app.Flask.after_request`
    8.  :func:`~flask.app.Flask.teardown_request`


.. [#] https://docs.python.org/3/library/asyncio-task.html#coroutines
