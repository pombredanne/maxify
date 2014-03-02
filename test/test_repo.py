"""Unit tests for the `maxify.repo` module.

"""

import pytest

from maxify.repo import *
from maxify.units import *


def test_projects_all(project):
    projects = Projects().all()

    assert project in projects


def test_projects_all_named(project, org1_project):
    names = [project.qualified_name, org1_project.qualified_name]

    projects = Projects().all_named(*names)

    assert len(projects) == 2

    ids = {p.id for p in projects}
    assert project.id in ids
    assert org1_project.id in ids


def test_projects_matching_name(project, org1_project):
    partial_name = project.name[:4]
    projects = Projects()
    matches = projects.matching_name(partial_name)
    assert len(matches) == 1
    assert project.name in matches

    partial_name = org1_project.organization

    matches = projects.matching_name(partial_name)
    assert len(matches) == 1
    assert Projects.qualified_name(org1_project.name,
                                   org1_project.organization) in matches

    matches = projects.matching_name("blah")
    assert not len(matches)


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


def test_project_delete(project):
    projects = Projects()
    projects.delete(project)

    persisted_project = projects.get(project.name, project.organization)
    assert persisted_project is None