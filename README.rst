Stiny
=====

Home automation assistant

Structure
---------
The core webserver is a WSGI app running the pyramid framework. Those are the
``stiny/*.py`` files. The webserver also starts a worker thread (in
``stiny/worker.py``) that interfaces with the relays. The only webpage rendered
by the python app is inside ``stiny/templates/index.jinja2``; all page changes
thereafter are loaded in via angular. Javascript/css libraries are in
``stiny/static/lib``, and the client-side application code is in
``stiny/static/app``.

Local Development
-----------------
First you need to download all the javascript/css libraries that we're using.
There's a handy script that will do just that:

``./dl-deps.sh``

Then you need to `install Go <https://golang.org/doc/install>`_. We're using an asset
pipeline that I wrote in Go to compile coffeescript and less, and to bundle
everything.

After you have Go, you need to install the asset pipeline:

``go get github.com/stevearc/pike``

Now create a virtualenv and install stiny:

.. code-block:: bash

    $ virtualenv stiny_env
    $ . stiny_env/bin/activate
    $ pip install -r requirements_dev.txt
    $ pip install -e .

Everything should be working! You can run the server with ``pserve --reload
development.ini``, and the asset pipeline with ``go run build.go -w``. For
convenience I have bundled both of those commands into the script
``./serve_forever.sh``

Deploy
------
You will need certain secret tokens to deploy. During the deploy process they
are read out of environment variables. I put them inside the google doc on door
wiring. You should put them into your bashrc or similar.

We're using fabric to deploy. All you need to do is run ``fab deploy``.
