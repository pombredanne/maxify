"""Unit tests for the ``maxify.stopwatch`` module.
"""

import time
from datetime import timedelta

import pytest

from maxify.stopwatch import StopWatch


def test_stopwatch():
    s = StopWatch()
    s.start()
    time.sleep(2)
    s.stop()

    assert timedelta(seconds=1) <= s.total <= timedelta(seconds=2)


def test_stopwatch_pause():
    s = StopWatch()
    s.start()
    time.sleep(1)
    s.pause()
    time.sleep(1)
    s.start()
    time.sleep(1)
    s.stop()

    assert timedelta(seconds=1) <= s.total <= timedelta(seconds=3)


def test_stopwatch_reset():
    s = StopWatch()
    s.start()
    time.sleep(1)
    s.reset()

    assert s.total == timedelta(seconds=0)


def test_stopwatch_restart():
    s = StopWatch()
    s.start()
    s.stop()
    with pytest.raises(RuntimeError):
        s.start()