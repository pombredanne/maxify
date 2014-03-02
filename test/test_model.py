"""
Unit tests for the ``maxify.model`` module.
"""

import pytest

from maxify.model import *


def test_open_user_data():
    session = open_user_data(":memory:", echo=False)
    assert session
    session.execute("SELECT 1")
    session.close()


def test_project_qualified_name():
    p = Project(name="maxify", organization="scopetastic")
    assert p.qualified_name == "scopetastic/maxify"

    p = Project(name="test")
    assert p.qualified_name == "test"


def test_project_split_qualified_name():
    assert Project.split_qualfied_name("scopetastic/maxify") == \
           ("scopetastic", "maxify")
    assert Project.split_qualfied_name("test") == (None, "test")


def test_project_task(project, db_session):
    task_name = "Test Task"
    test_desc = "Test Desc"
    t = project.task(task_name)
    t.desc = test_desc

    t2 = project.task(task_name)

    assert t == t2

    db_session.commit()

    project2 = db_session.query(Project).one()
    project2.unpack()

    t3 = project2.task(task_name)

    assert t3.desc == t.desc


def test_task_data_points(project,
                          story_points_metric,
                          db_session):
    task_name = "Test Task"
    t = project.task(task_name)
    t.update_data_points((story_points_metric, 5))

    db_session.commit()

    t2 = db_session.query(Task).filter_by(id=t.id).one()
    t2.unpack()

    assert t2.data_point(story_points_metric).value == 5


def test_data_points_update(project,
                            compile_time_metric,
                            db_session):
    task_name = "Test Task"
    t = project.task(task_name)
    t.update_data_points((compile_time_metric, "4 hrs"))

    db_session.commit()

    t2 = db_session.query(Task).filter_by(id=t.id).one()
    t2.unpack()

    assert t2.data_point(compile_time_metric).value == 14400

    t2.update_data_points((compile_time_metric, "1 hr"))

    assert t2.data_point(compile_time_metric).value == 3600


def test_data_points_valid_range(project,
                                 story_points_metric):
    task_name = "Test Task"
    t = project.task(task_name)
    with pytest.raises(ModelError):
        t.update_data_points((story_points_metric, 13))


def test_data_points_defaults(project,
                              story_points_metric,
                              compile_time_metric,
                              db_session):
    task_name = "Test Task"
    t = project.task(task_name)
    t.update_data_points(story_points_metric)

    assert t.data_point(story_points_metric).value == \
           story_points_metric.default_value

    db_session.commit()

    t2 = db_session.query(Task).filter_by(id=t.id).one()
    t2.unpack()

    assert t2.data_point(story_points_metric).value == \
           story_points_metric.default_value

    task_name = "Test Task 2"
    t = project.task(task_name)

    t.update_data_points(compile_time_metric)

    assert t.data_point(compile_time_metric).value is None