"""
Unit tests for the ``maxify.config`` module.
"""
import pytest

from maxify.config import *


def test_metric():
    # Test valid Metric
    metric = Metric(name="Test metric",
                    units=Int,
                    desc="Sample desc",
                    value_range=["A", "B", "C"],
                    default_value="A")

    assert metric

    # Test invalid Metric
    with pytest.raises(ConfigError):
        Metric(name="Test failure metric",
               units=str)

    with pytest.raises(ConfigError):
        Metric(name="Test failure metric",
               units="string")


def test_project():
    p = Project(name="Test Project",
                nickname="test",
                desc="Test Description",
                prop1="A",
                prop2="B")

    assert p.prop1 == "A", "Mixed in property not valid"
    assert p.prop2 == "B", "Mixed in property not valid"


def test_project_add_metric():
    p = Project(name="Test Project",
                nickname="test",
                desc="Test Description")
    p.add_metric(name="Story Points",
                 units=Int,
                 desc="Estimated story points")

    with pytest.raises(ConfigError):
        p.add_metric(name="Story Points",
                     units=Int,
                     desc="Estimated story points")

    with pytest.raises(ConfigError):
        p.add_metric(name="Bad metric",
                     units=str)


def test_load_config():
    test_dir = os.path.dirname(__file__)
    load_config(os.path.join(test_dir, "conf.py"))

    project = Project.project("NEP")
    assert project

    sample_metric = project.metric("Research Time")
    assert sample_metric
    assert sample_metric.units == Duration


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