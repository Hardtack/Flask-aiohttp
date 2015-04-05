First of All
============

First of all, you can use this extension like another plain Flask extensions.

For example, You can initialize the extension like ::

    from flask import Flask
    from flask.ext.aiohttp import AioHTTP

    app = Flask(__name__)

    aio = AioHTTP(app)

or you can initialize it later ::

    from flask import Flask
    from flask.ext.aiohttp import AioHTTP

    def create_app():
        app = Flask(__name__)
        aio.init_app(app)

    aio = AioHTTP()

But, its application running method is different then plain Flask apps one.
You have to run it on the asyncio's run loop. ::

    if __name__ == '__main__':
        aio.run(app)

You can also debug it using werkzeug debugger ::

    if __name__ == '__main__':
        aio.run(app, debug=True)

You can use gunicorn using aiohttp

In myapp.py (or some module name you want to use) ::

    from you_application_module import app as flask_app

    app = flask_app.aiohttp_app

And run gunicorn by ::

    gunicorn myapp:app -k aiohttp.worker.GunicornWebWorker -b localhost:8080
