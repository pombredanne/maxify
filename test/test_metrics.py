"""Unit tests for the ``maxify.metrics`` module.
"""

from datetime import timedelta
from decimal import Decimal

import pytest

from maxify.data import open_user_data
from maxify.projects import Project, Task
from maxify.metrics import (
    Metric,
    Duration,
    Number,
    ParsingError
)

@pytest.fixture
def metrics_session(request):
    session = open_user_data(":memory:", use_static_pool=True)
    request.addfinalizer(session.close)
    return session


@pytest.fixture
def mock_project(metrics_session):
    project = Project(name="mock_project")
    metrics_session.add(project)
    metrics_session.commit()
    return project


@pytest.fixture
def number_metric(metrics_session, mock_project):
    metric = Metric(name="points",
                    metric_type=Number,
                    project=mock_project)
    metrics_session.add(metric)
    metrics_session.commit()
    return metric


@pytest.fixture
def duration_metric(metrics_session, mock_project):
    metric = Metric(name="time",
                    metric_type=Duration,
                    project=mock_project)
    metrics_session.add(metric)
    metrics_session.commit()
    return metric


@pytest.fixture
def mock_task(metrics_session, mock_project):
    task = Task(name="mock_task", project=mock_project)
    metrics_session.add(task)
    metrics_session.commit()
    return task


def test_number(metrics_session,
                number_metric,
                mock_task):
    entry1 = Number(number_metric, mock_task, Decimal("5"))

    metrics_session.add(entry1)
    metrics_session.commit()

    total = Number.total(number_metric, mock_task, metrics_session)
    assert total == Decimal("5")


def test_duration(metrics_session,
                  duration_metric,
                  mock_task):
    entry1 = Duration(duration_metric, mock_task, timedelta(hours=1))
    entry2 = Duration(duration_metric, mock_task, timedelta(hours=2))

    metrics_session.add(entry1)
    metrics_session.add(entry2)

    metrics_session.commit()

    # Test aggregation
    total_duration = Duration.total(duration_metric, mock_task, metrics_session)
    assert isinstance(total_duration, timedelta)
    assert total_duration == timedelta(hours=3)

    # Test individual metrics
    persisted_1 = metrics_session.query(Duration)\
        .filter_by(metric_id=duration_metric.id,
                   task_id=mock_task.id,
                   id=entry1.id)\
        .one()
    persisted_2 = metrics_session.query(Duration) \
        .filter_by(metric_id=duration_metric.id,
                   task_id=mock_task.id,
                   id=entry2.id) \
        .one()

    assert persisted_1.value == timedelta(hours=1)
    assert persisted_2.value == timedelta(hours=2)


def test_number_delete(metrics_session,
                       number_metric,
                       mock_task):
    entry1 = Number(number_metric, mock_task, Decimal("5"))

    metrics_session.add(entry1)
    metrics_session.commit()

    assert metrics_session.query(Number).count() == 1

    metrics_session.delete(mock_task)
    metrics_session.commit()

    assert metrics_session.query(Number).count() == 0


def test_duration_delete(metrics_session,
                         duration_metric,
                         mock_task):
    entry1 = Duration(duration_metric, mock_task, timedelta(hours=1))
    entry2 = Duration(duration_metric, mock_task, timedelta(hours=2))

    metrics_session.add(entry1)
    metrics_session.add(entry2)

    metrics_session.commit()

    assert metrics_session.query(Duration).count() == 2

    metrics_session.delete(mock_task)
    metrics_session.commit()

    assert metrics_session.query(Duration).count() == 0


def test_metric_delete(metrics_session,
                       number_metric,
                       mock_task):
    entry1 = Number(number_metric, mock_task, Decimal("5"))

    metrics_session.add(entry1)
    metrics_session.commit()

    assert metrics_session.query(Number).count() == 1

    metrics_session.delete(number_metric)
    metrics_session.commit()

    assert metrics_session.query(Number).count() == 0


def test_parse_number():
    value = Number.parse("500")
    assert value == Decimal(500)

    value = Number.parse("500.5")
    assert value == Decimal("500.5")

    with pytest.raises(ParsingError):
        Number.parse("5a")


def test_duration_timefmt():
    value = Duration.parse("10:05:01")
    assert value == timedelta(hours=10, minutes=5, seconds=1)

    value = Duration.parse("10:05")
    assert value == timedelta(hours=10, minutes=5)


def test_duration_hours():
    value = Duration.parse("4 hours")
    assert value == timedelta(hours=4)

    value = Duration.parse("4.5 hours")
    assert value == timedelta(hours=4, minutes=30)


def test_duration_minutes():
    value = Duration.parse("4 minutes")
    assert value == timedelta(minutes=4)

    value = Duration.parse("4.5 mins")
    assert value == timedelta(minutes=4, seconds=30)


def test_duration_seconds():
    value = Duration.parse("4.5 seconds")
    assert value == timedelta(seconds=4, milliseconds=500)

    value = Duration.parse("525s")
    assert value == timedelta(seconds=525)


def test_duration_days():
    value = Duration.parse("2 days")
    assert value == timedelta(days=2)


def test_duration_multiple():
    value = Duration.parse("2 hrs, 5 mins")
    assert value == timedelta(hours=2, minutes=5)


def test_to_str():
    assert Number.to_str(1) == "1"
    assert Number.to_str(1000) == "1,000"
    assert Number.to_str(10000) == "10,000"
    assert Number.to_str(1000000) == "1,000,000"

    assert Number.to_str(1000.0) == "1,000"
    assert Number.to_str(1500.56) == "1,500.56"

    assert Duration.to_str(timedelta(days=1)) == "1 day, 0:00:00"
    assert Duration.to_str(timedelta(days=1, minutes=1, seconds=40)) == \
        "1 day, 0:01:40"
    assert Duration.to_str(timedelta(minutes=5, seconds=5)) == "0:05:05"