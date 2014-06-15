"""Module containing logic for implementing stop watches that can be used
to record time for a maxify task.
"""

from datetime import timedelta
from threading import Timer


class StopWatch(object):
    """Object used to measure a duration of time like a stop watch.
    """
    resolution = 1.0

    def __init__(self):
        #: Total number of seconds recorded by the stopwatch.
        self.total_secs = 0
        #: Boolean indicating the timer has stopped
        self.stopped = False
        self._timer = None

    def start(self):
        """Starts the stop watch.  This can either start the stop watch for
        the first time or be used to resume recording after it is paused.
        """
        if self.stopped:
            raise RuntimeError("Stop watch has been stopped, it can't be "
                               "started again.")
        self._timer_tick()

    def stop(self):
        """Stops the stop watch.  Once stopped, the stop watch cannot be
        restarted.
        """
        self.pause()
        self.stopped = True

    def pause(self):
        """Pauses the stop watch.  To restart recording, call the ``start``
        method again.
        """
        self._timer.cancel()

    def reset(self):
        """Resets the stop watch.  This will pause the stop watch and set the
        total time recorded back to 0.

        """
        self.pause()
        self.total_secs = 0

    @property
    def total(self):
        """The total amount of time recorded by the stopwatch as a
        :class:`datetime.timedelta` object.
        """
        return timedelta(seconds=self.total_secs)

    def _timer_tick(self):
        if self._timer is not None:
            self.total_secs += self.resolution
            pass

        self._timer = Timer(self.resolution, self._timer_tick)
        self._timer.start()