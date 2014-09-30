import time

import logging
from functools import wraps
from multiprocessing import Queue
from threading import Thread


LOG = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    LOG.warn("Not running on Raspberry Pi; controls unavailable")


def async(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        t = Thread(target=function, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
        return t
    return wrapper


class BaseWorker(Thread):

    """
    Worker thread that interfaces with relays.

    The only safe method to call from another thread is :meth:`~.do`.

    Parameters
    ----------
    calendar : :class:`stiny.gutil.Calendar`
        Stiny wrapper for Google Calendar API
    in_map : dict, optional
        Mapping for names of input relays to the relay index
    out_map : dict, optional
        Mapping for names of output relays to the relay index
    isolate : bool, optional
        If True, don't attempt to send signals to the relays. Useful for local
        development (default False)
    input_throttle : float, optional
        Relay states may change at most once per this time range (default 0.1)

    """

    def __init__(self, *args, **kwargs):
        self.cal = kwargs.pop('calendar')
        self._isolate = kwargs.pop('isolate', False)
        self._in_map = kwargs.pop('in_map', {})
        self._out_map = kwargs.pop('out_map', {})
        self._input_throttle = kwargs.pop('input_throttle', 0.1)
        super(BaseWorker, self).__init__(*args, **kwargs)
        self._msg_queue = Queue()
        self._state = {key: False for key in self._out_map}
        self._last_read_time = {}
        self._btn_states = {}

    def setup(self):
        """ Initialize the relays. """
        if self._isolate:
            return
        GPIO.setmode(GPIO.BCM)
        for idx in self._out_map.values():
            GPIO.setup(idx, GPIO.OUT)
        for idx in self._in_map.values():
            GPIO.setup(idx, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def _write(self, relay, on):
        """ Write a state to a relay. """
        if self._isolate:
            return False
        GPIO.output(self._out_map[relay], 1 if on else 0)

    def _get(self, relay):
        """
        Get on/off state from an input.

        Returns
        -------
        on : bool

        """
        if self._isolate:
            return False
        return not GPIO.input(self._in_map[relay])

    def _get_input(self, relay):
        """
        Get throttled state of input.

        Returns
        -------
        changed : bool
            True if the state is different from last call.
        on : bool

        """
        now = time.time()
        # Sometimes the input switches jitter, so throttle the changes.
        if self._last_read_time.get(relay, 0) + self._input_throttle > now:
            return False, None
        self._last_read_time[relay] = now
        state = self._get(relay)
        changed = state != self._btn_states.get(relay)
        self._btn_states[relay] = state
        return changed, state

    def _listen_for_inputs(self):
        """ Check all inputs and queue commands if activated. """
        for name in self._in_map:
            changed, state = self._get_input(name)
            if changed:
                method_name = 'on_%s' % name
                LOG.debug("Received input %s", method_name)
                meth = getattr(self, method_name, None)
                if meth is None:
                    LOG.warning("Unhandled input %r", method_name)
                    continue
                try:
                    meth(state)
                except TypeError:
                    LOG.exception("Bad arguments")

    def _process_messages(self):
        """ Process all messages in the queue. """
        requeue = []
        while not self._msg_queue.empty():
            msg = self._msg_queue.get()

            # If the message has a start time, it might not be time to run it
            # yet. Requeue it after processing other messages.
            if 'run_after' in msg and time.time() < msg['run_after']:
                requeue.append(msg)
                continue

            method_name = 'do_%s' % msg['command']
            LOG.debug("Running %s, %s", method_name, msg['data'])
            meth = getattr(self, method_name, None)
            if meth is None:
                LOG.error("Bad command %r", method_name)
                continue
            try:
                meth(**msg['data'])
            except TypeError:
                LOG.exception("Bad arguments")

        for msg in requeue:
            self._msg_queue.put(msg)

    def do_on(self, relay):
        """ Turn a relay on. """
        self._state[relay] = True

    def do_off(self, relay):
        """ Turn a relay off. """
        self._state[relay] = False

    def do_on_off(self, relay, duration):
        """
        Turn a relay on, then off.

        Parameters
        ----------
        relay : str
            Name of the relay.
        duration : float
            Number of seconds to keep relay on.

        """
        self.do_on(relay)
        self.do('off', delay=duration, relay=relay)

    def do(self, command, delay=None, run_after=None, **kwargs):
        """
        Thread-safe way to enqueue a message.

        Parameters
        ----------
        command : str
            Name of command. Will run the method "do_[command]".
        delay : float, optional
            Wait for this many seconds, then run the command.
        run_after : float, optional
            Unix timestamp. Will wait until this time before running the
            command.
        **kwargs : dict, optional
            Pass these arguments to the method being run.

        """
        if delay is not None and run_after is not None:
            raise TypeError("Cannot specify 'delay' and 'run_after'")

        msg = {
            'command': command,
            'data': kwargs,
        }
        if delay is not None:
            msg['run_after'] = time.time() + delay
        elif run_after is not None:
            msg['run_after'] = run_after
        self._msg_queue.put(msg)

    def run(self):
        self.setup()
        while True:
            self._listen_for_inputs()
            self._process_messages()

            if not self._isolate:
                for relay, on in self._state.iteritems():
                    self._write(relay, on)

            time.sleep(0.01)


class DoorWorker(BaseWorker):

    """ Worker for the door buzzer and doorbell relays.  """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('out_map', {
            'doorbell': 7,
            'outside_latch': 4,
        })
        kwargs.setdefault('in_map', {
            'doorbell_button': 22,
            'buzzer': 23,
        })
        super(DoorWorker, self).__init__(*args, **kwargs)

    def on_doorbell_button(self, state):
        """
        Ring doorbell when doorbell is pressed.

        If in party mode, also open the door.

        """
        self.do('on' if state else 'off', relay='doorbell')
        if not state:
            self._open_if_party()

    @async
    def _open_if_party(self):
        if self.cal.is_party_time():
            self.do('on_off', delay=4, duration=3,
                    relay='outside_latch')

    def on_buzzer(self, state):
        """ Open the door when buzzer is pressed """
        self.do('on' if state else 'off', relay='outside_latch')
