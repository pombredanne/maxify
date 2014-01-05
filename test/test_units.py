"""
Unit tests for the ``maxify.units`` module.
"""

import pytest

from maxify.units import *


def test_int():
    value = Int.parse("500")
    assert value == Decimal(500)

    with pytest.raises(ParsingError):
        Int.parse("500.5")


def test_float():
    value = Float.parse("500.5")
    assert value == Decimal("500.5")

    with pytest.raises(ParsingError):
        Float.parse("5a")


def test_duration_timefmt():
    value = Duration.parse("10:05:01")
    assert value == 36301

    value = Duration.parse("10:05")
    assert value == 36300


def test_duration_hours():
    value = Duration.parse("4 hours")
    assert value == Decimal("14400")

    value = Duration.parse("4.5 hours")
    assert value == Decimal("16200")


def test_duration_minutes():
    value = Duration.parse("4 minutes")
    assert value == Decimal("240")

    value = Duration.parse("4.5 mins")
    assert value == Decimal("270")


def test_duration_seconds():
    value = Duration.parse("seconds 4.5")
    assert value == Decimal("4.5")

    value = Duration.parse("525s")
    assert value == Decimal(525)


def test_duration_days():
    value = Duration.parse("2 days")
    assert value == Decimal(172800)


def test_duration_multiple():
    value = Duration.parse("2 hrs, 5 mins")
    assert value == Decimal(7500)

    value = Duration.parse("hrs 2, 5 mins")
    assert value == Decimal(7500)