import time
from .models import State
from datetime import datetime

import logging
from multiprocessing import Queue
from threading import Thread


LOG = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    LOG.warn("Not running on Raspberry Pi; controls unavailable")

OUT_MAP = {
    'doorbell': 7,
    'outside_latch': 4,
}
IN_MAP = {
    'doorbell_button': 22,
    'buzzer': 23,
}
INPUT_THROTTLE = 0.1

class Worker(Thread):
    def __init__(self, *args, **kwargs):
        self.db = kwargs.pop('engine')
        self._isolate = kwargs.pop('isolate', False)
        super(Worker, self).__init__(*args, **kwargs)
        self._msg_queue = Queue()
        self._state = {key: False for key in OUT_MAP}
        self._last_read_time = {}
        self._btn_states = {}

    def setup(self):
        if self._isolate:
            return
        GPIO.setmode(GPIO.BCM)
        for idx in OUT_MAP.values():
            GPIO.setup(idx, GPIO.OUT)
        for idx in IN_MAP.values():
            GPIO.setup(idx, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def _write(self, relay, on):
        if self._isolate:
            return False
        GPIO.output(OUT_MAP[relay], 1 if on else 0)

    def _get(self, relay):
        if self._isolate:
            return False
        return not GPIO.input(IN_MAP[relay])

    def _get_input(self, relay):
        now = time.time()
        # Sometimes the input switches jitter, so throttle the changes.
        if self._last_read_time.get(relay, 0) + INPUT_THROTTLE > now:
            return False, None
        self._last_read_time[relay] = now
        state = self._get(relay)
        changed = state != self._btn_states.get(relay)
        self._btn_states[relay] = state
        return changed, state

    def _listen_for_inputs(self):
        changed, state = self._get_input('doorbell_button')
        if changed:
            now = datetime.utcnow()
            party_mode = False
            for party in self.db(State).filter(State.start < now, name='party').gen():
                if now < party.end:
                    party_mode = True
                    break
            if party_mode and state:
                self.do('on_off', delay=4, duration=3, relay='outside_latch')
            self.do('on' if state else 'off', relay='doorbell')

        changed, state = self._get_input('buzzer')
        if changed:
            self.do('on' if state else 'off', relay='outside_latch')

    def _process_messages(self):
        requeue = []
        while not self._msg_queue.empty():
            msg = self._msg_queue.get()

            if 'run_after' in msg and time.time() < msg['run_after']:
                requeue.append(msg)
                continue

            method_name = 'do_%s' % msg['command']
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
        self._state[relay] = True

    def do_off(self, relay):
        self._state[relay] = False

    def do_on_off(self, relay, duration):
        self.do_on(relay)
        self.do('off', delay=duration, relay=relay)

    def do(self, command, delay=None, run_after=None, **kwargs):
        """ Thread-safe way to enqueue a message """
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
