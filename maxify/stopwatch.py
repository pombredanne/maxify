"""Module containing logic for implementing stop watches that can be used
to record time for a maxify task.
"""

from datetime import timedelta
from threading import Timer
from maxify.log import Logger


class StopWatch(object):
    """Object used to measure a duration of time like a stop watch.
    """
    resolution = 1.0

    STATUS_RUNNING = "Running"
    STATUS_STOPPED = "Stopped"
    STATUS_PAUSED = "Paused"
    STATUS_RESET = "Reset"

    log = Logger("stopwatch")

    def __init__(self):
        #: Total number of seconds recorded by the stopwatch.
        self.total_secs = 0
        #: Boolean indicating the timer has stopped
        self.stopped = False
        self._timer = None
        self._status = "Stopped"
        self._tick_callback = None

    def start(self, tick_callback=None):
        """Starts the stop watch.  This can either start the stop watch for
        the first time or be used to resume recording after it is paused.

        :param tick_callback: Function that will be called on each tick
            of the stopwatch.  This can be used for things like output displays.
        """
        if self.stopped:
            raise RuntimeError("Stop watch has been stopped, it can't be "
                               "started again.")

        if tick_callback and not callable(tick_callback):
            raise ValueError("Tick callback must be callable.")

        self._tick_callback = tick_callback
        self._status = self.STATUS_RUNNING
        self._timer_tick()

    def stop(self):
        """Stops the stop watch.  Once stopped, the stop watch cannot be
        restarted.
        """
        if self._timer:
            self.pause()
        self._status = self.STATUS_STOPPED
        self.stopped = True
        self._handle_tick_callback()

    def pause(self):
        """Pauses the stop watch.  To restart recording, call the ``start``
        method again.
        """
        self._status = self.STATUS_PAUSED
        self._timer.cancel()
        self._handle_tick_callback()

    def reset(self):
        """Resets the stop watch.  This will pause the stop watch and set the
        total time recorded back to 0.

        """
        self.pause()
        self._status = self.STATUS_RESET
        self.total_secs = 0
        self._handle_tick_callback()

    @property
    def total(self):
        """The total amount of time recorded by the stopwatch as a
        :class:`datetime.timedelta` object.
        """
        return timedelta(seconds=self.total_secs)

    def _timer_tick(self):
        if self._timer is not None:
            self.total_secs += self.resolution
            self._handle_tick_callback()

        self._timer = Timer(self.resolution, self._timer_tick)
        self._timer.start()

    def _handle_tick_callback(self):
        if self._tick_callback:
            try:
                self._tick_callback(self.total, self._status)
            except Exception as e:
                self.log.exception("Exception occurred in tick callback", e)
                self._tick_callback = None
                return
