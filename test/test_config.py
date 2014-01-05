"""
Unit tests for the ``maxify.config`` module.
"""
import pytest

from maxify.config import *
from maxify.units import *


@pytest.fixture(autouse=True)
def project_reset():
    Project._projects = {}
    Project._project_nicknames = {}


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


def test_projects():
    Project(name="Test Project 10",
            nickname="test",
            desc="Test Description")

    Project(name="Test Project 2",
            nickname="test2",
            desc="Test 2 Description")

    Project(name="Final Test Project",
            nickname="final",
            desc="Final test project")

    projects = Project.projects()

    assert len(projects) == 3
    assert projects[0].nickname == "final"
    assert projects[2].nickname == "test"


def test_load_config():
    test_dir = os.path.dirname(__file__)
    load_config(os.path.join(test_dir, "conf.py"))

    project = Project.project("NEP")
    assert project

    sample_metric = project.metric("Research Time")
    assert sample_metric
    assert sample_metric.units == Duration