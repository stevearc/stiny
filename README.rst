Stiny
=====
Home automation assistant

Calendar Interface
------------------
Note: Calendar events should all have a start and end time. All-day events will
have some weirdness due to PST vs UTC timezones.

Adding a Guest
^^^^^^^^^^^^^^
To add a guest, create any event on the calendar. In the description, put the following:

``guest: guestemail@addr.com, (555) 555-5555``

You may add multiple guests (one guest per line), and you may add any number of
emails/phone numbers per guest (comma-separated). The email is for website
access, the phone number is for twilio SMS access (format is unimportant, it
strips out all non-digit characters).

Scheduling a Party
^^^^^^^^^^^^^^^^^^
Create any event with 'party' (case-insensitive) in the title.

Structure
---------
The core webserver is a WSGI app running the pyramid framework. Those are the
``stiny/*.py`` files. The webserver is designed to run on a machine separate
from the raspberry pi relay controller. The pi runs worker code (in
``worker/``) that creates a simple http interface for controls. We then use ssh
to forward a port to the webserver so the webserver can send commands to the
pi.

More on the webserver: the only webpage rendered by the python app is inside
``stiny/templates/index.jinja2``; all page changes thereafter are loaded in via
angular. Javascript/css libraries are in ``stiny/static/lib``, and the
client-side application code is in ``stiny/static/app``.

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

To run the worker code, just do ``python worker/``.

Deploy
------
You will need certain secret tokens to deploy. During the deploy process they
are read out of environment variables. I put them inside the google doc on door
wiring. You should put them into your bashrc or similar.

We're using fabric to deploy. Do ``fab help`` to get a list of commands. You
will probably only ever need ``fab deploy_web`` and ``fab deploy_door``.
