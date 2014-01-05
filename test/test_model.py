"""
Unit tests for the ``maxify.model`` module.
"""

import pytest

from maxify.config import *
from maxify.model import *
from maxify.units import *


@pytest.fixture(scope="module")
def project():
    p = Project(name="Test Project",
                desc="A test project")
    p.add_metric(name="Story Points",
                 units=Int)
    p.add_metric(name="Coding Hours",
                 units=Duration)

    return p


@pytest.fixture(scope="module")
def story_points_metric(project):
    return project.metric("Story Points")


@pytest.fixture
def db_session():
    return open_user_data(":memory:", True)


def test_data_point(project,
                    story_points_metric,
                    db_session):
    point = DataPoint(project.name  ,
                      story_points_metric.name,
                      5)
    db_session.add(point)
    db_session.commit()

    persisted_point = db_session.query(DataPoint).filter_by(id=point.id).one()

    assert persisted_point.project == point.project

    point = DataPoint(project,
                      story_points_metric,
                      Decimal("5.5"))
    db_session.add(point)
    db_session.commit()


def test_invalid_data_point(project,
                            story_points_metric,
                            db_session):
    with pytest.raises(BaseException):
        point = DataPoint(project,
                          story_points_metric,
                          [1, 2, 3])
        db_session.add(point)
        db_session.commit()

    db_session.rollback()

    with pytest.raises(BaseException):
        point = DataPoint(None, None, None)
        db_session.add(point)
        db_session.commit()

    db_session.rollback()

    with pytest.raises(BaseException):
        point = DataPoint(project, None, None)
        db_session.add(point)
        db_session.commit()


def test_task(project,
              story_points_metric,
              db_session):
    task = Task(project,
                "Task 1")
    task.update_data_point(story_points_metric, 5)

    db_session.add(task)
    db_session.commit()

    assert task.data_point_value(story_points_metric) == 5

    persisted_task = db_session.query(Task).filter_by(id=task.id).one()
    assert persisted_task.data_point_value(story_points_metric) == 5

    task.update_data_point(story_points_metric, 10)

    db_session.commit()

    assert task.data_point_value(story_points_metric) == 15

    persisted_task = db_session.query(Task).filter_by(id=task.id).one()
    assert persisted_task.data_point_value(story_points_metric) == 15
