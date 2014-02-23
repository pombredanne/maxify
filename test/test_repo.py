"""Unit tests for the `maxify.repo` module.

"""

import pytest

from maxify.repo import *
from maxify.units import *

@pytest.fixture
def org1_project(db_session):
    p = Project(name="org1_project",
                organization="org1",
                desc="Org1 Project")

    p.add_metric(Metric(
        name="Story Points",
        units=Int,
        value_range=[1, 2, 3, 5, 8],
        default_value=3
    ))

    p.add_metric(Metric(
        name="Compile Time",
        units=Duration
    ))

    db_session.add(p)
    db_session.commit()

    return p


def test_projects_all(project):
    projects = Projects().all()

    assert project in projects


def test_projects_get(project, org1_project):
    projects = Projects()

    persisted_project = projects.get(project.name, project.organization)
    assert persisted_project.id == project.id

    persisted_project = projects.get(org1_project.name,
                                     org1_project.organization)
    assert persisted_project.id == org1_project.id

    persisted_project = projects.get(org1_project.organization +
                                     "/" +
                                     org1_project.name)
    assert persisted_project.id == org1_project.id

    persisted_project = projects.get("fakename")
    assert persisted_project is None


def test_project_save(project):
    projects = Projects()
    project.desc = "Sample desc"

    projects.save(project)

    persisted_project = projects.get(project.name, project.organization)
    assert persisted_project.desc == project.desc


def test_project_unpacked(project, story_points_metric):
    projects = Projects()
    task = project.task("Task1")
    task.update_data_points((story_points_metric, 5))
    projects.save(project)

    persisted_project = projects.get(project.name, project.organization)
    persisted_task = persisted_project.task("Task1")

    assert persisted_task.data_point(story_points_metric).value == 5