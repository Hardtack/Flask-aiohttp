Flask-aiohttp --- Asynchronous Flask application with aiohttp.
==============================================================

**Flask-aiohttp** adds asyncio_ &
`websocket <http://en.wikipedia.org/wiki/WebSocket>`_ [#]_ support to Flask
using aiohttp_.

.. _asyncio: https://docs.python.org/3/library/asyncio.html
.. _aiohttp: https://aiohttp.readthedocs.org/

For example ::

    @app.route('/use-external-api')
    @async
    def use_external_api():
        response = yield from aiohttp.request(
            'GET', 'https://api.example.com/data/1')
        data = yield from response.read()

        return data

You can find more guides from following list:

.. toctree::
   :maxdepth: 1

   firstofall
   coroutine
   websocket

API

.. toctree::
   :maxdepth: 1

   api/modules


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. [#] http://aiohttp.readthedocs.org/en/v0.15.1/web.html#websockets
