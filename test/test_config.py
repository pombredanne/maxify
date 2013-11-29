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
                    range=["A", "B", "C"],
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
                desc="Test Description",
                prop1="A",
                prop2="B")

    assert p.prop1 == "A", "Mixed in property not valid"
    assert p.prop2 == "B", "Mixed in property not valid"


def test_project_add_metric():
    p = Project(name="Test Project",
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