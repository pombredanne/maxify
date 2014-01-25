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
    p.add_metric(name="Research Time",
                 units=Duration)
    p.add_metric(name="Notes",
                 units=String)

    return p


@pytest.fixture(scope="module")
def story_points_metric(project):
    return project.metric("Story Points")


@pytest.fixture(scope="module")
def notes_metric(project):
    return project.metric("Notes")


@pytest.fixture
def db_session():
    return open_user_data(":memory:", True)


@pytest.fixture
def project_store(project,
                  db_session):
    return ProjectStore(project, db_session)


@pytest.fixture
def sample_task(project_store, story_points_metric):
    return project_store.update_task("Task 2",
                                     desc="Test task",
                                     metrics=[(story_points_metric, 5)])


def test_data_point_numeric(project,
                            story_points_metric,
                            db_session):
    point = DataPoint(project.name,
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


def test_task_str_metric(project, notes_metric, db_session):
    task = Task(project, "String task")
    task.update_data_point(notes_metric, "abcdefg")

    db_session.add(task)
    db_session.commit()

    assert task.data_point_value(notes_metric) == "abcdefg"

    persisted_task = db_session.query(Task).filter_by(id=task.id).one()
    assert persisted_task.data_point_value(notes_metric) == "abcdefg"


def test_task_invalid_project():
    with pytest.raises(ModelError):
        Task(500, "Test task")


def test_project_store(project,
                       project_store):
    assert project_store.project_id == project.name
    assert len(project_store.tasks) == 0


def test_project_store_create_task(sample_task, story_points_metric):
    assert sample_task.name == "Task 2"
    assert sample_task.desc == "Test task"
    assert sample_task.data_point_value(story_points_metric) == 5


def test_project_store_task(project_store, sample_task):
    assert project_store.task("Not there") is None
    assert project_store.task(sample_task.name)


def test_project_store_update_task(project_store,
                                   story_points_metric,
                                   sample_task):
    updated_task = project_store.update_task(sample_task.name,
                                             metrics=[(story_points_metric,
                                                       10)])

    assert updated_task.data_point_value(story_points_metric) == 15
    assert project_store.task(sample_task.name)\
        .data_point_value(story_points_metric) == 15