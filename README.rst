Stiny
=====
Home automation assistant

Calendar Interface
------------------
Note: Calendar events should all have a start and end time. All-day events will
have some weirdness due to PST vs UTC timezones.

Adding a Guest
^^^^^^^^^^^^^^
To add a guest, create any event on the calendar. You can either invite the
guest to the event, or put the following in the description:

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
``stiny_worker/``) that creates a simple http interface for controls. We then
use ssh to forward a port to the webserver so the webserver can send commands to
the pi.

Local Development
-----------------

Now create a virtualenv and install stiny:

.. code-block:: bash

    $ virtualenv venv
    $ . venv/bin/activate
    $ pip install -r requirements_dev.txt
    $ pip install -e .
    $ pip install -e stiny_worker

Also set up the node package

.. code-block:: bash

    $ npm install

You will need certain secret tokens for accessing certain APIs (GCal, Twilio,
etc). They will be read out of environment variables. You should put them into
your bashrc or some other file you can conveniently source before doing
development::

  STINY_ENCRYPT_KEY - Secret key used to encrypt the beaker session
  STINY_VALIDATE_KEY - Secret key used to validate the beaker session
  STINY_AUTH_SECRET - Secret key used to sign the auth token
  STINY_PROD_CLIENT_GOOGLE_CLIENT_ID - Oauth 2.0 'web application' client ID configured for your production site
  STINY_DEV_CLIENT_GOOGLE_CLIENT_ID - Oauth 2.0 'web application' client ID configured for localhost development
  STINY_SERVER_GOOGLE_CLIENT_ID - Oauth 2.0 'other' client ID used to get calendar access permissions
  STINY_SERVER_GOOGLE_CLIENT_SECRET - Corresponding secret for the STINY_SERVER_GOOGLE_CLIENT_ID
  STINY_TWILIO_AUTH_TOKEN - Auth token for twilio
  STINY_ADMINS - Space-delimited list of emails for admin users
  STINY_GUESTS - Space-delimited list of emails for users with unlock permissions
  STINY_PHONE_ACCESS - Space-delimited list of phone numbers for users with unlock permissions
  STINY_CAL_ID - Id of the calendar to check for events and guests

Activate the virtualenv and run ``stiny-setup``. This will create the
``credentials.dat`` file which will allow stiny to access the Google Calendar.

Everything should be working! You can run the server with ``pserve --reload
development.ini``, the asset pipeline with ``npm run watch``, and the worker
with ``stiny-worker --debug -l debug -i``.

Deploy
------
We're using fabric to deploy. Do ``fab help`` to get a list of commands. You
will probably only ever need ``fab deploy_web`` and ``fab deploy_door``.
