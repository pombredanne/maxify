"""Unit tests for the ``maxify.metrics`` module.
"""

from datetime import timedelta
from decimal import Decimal
import uuid

from sqlalchemy import Column
import pytest

from maxify.data import open_user_data, Base, GUID
from maxify.projects import Project, Task
from maxify.metrics import (
    Metric,
    Duration,
    Number
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