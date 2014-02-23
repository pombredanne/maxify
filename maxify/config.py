"""
Module defines import utility for importing project configuration from
a file into the user's data store.

"""

import imp
import os
from sqlalchemy.orm.exc import NoResultFound

try:
    from enum import Enum
except ImportError:
    from maxify.utils import Enum

import yaml
from logbook import Logger

from maxify.model import Project, Metric
from maxify.repo import Projects
from maxify import units

log = Logger("config")


class ConfigError(BaseException):
    """Type of error generated due to a configuration error, such as defining
    invalid units or metrics.
    """
    pass


class ProjectConflictError(BaseException):
    pass


#: Type of import strategy for configuration importing
ImportStrategy = Enum("ImportStrategy", ["abort", "merge", "overwrite"])


def import_config(path, import_strategy=ImportStrategy.abort):
    """Load project and metric configuration from the file specified and
    import into user's data file.

    :param path: `str` containing path to the configuration file.
    :param import_strategy: :class:`ImportStrategy` enum value indicating the
        import strategy to use in case a conflict is detected.

    :raise `ConfigError` Raised if invalid configuration file is found.

    """
    log.info("Attempting configuration import. Path: {} Stategy: {}",
             path,
             import_strategy)

    if not path or not os.path.exists(path):
        raise ConfigError("Path {} is not a valid file".format(path))

    # Load projects from file
    if path.endswith(".py"):
        projects = _load_python_config(path)
    elif path.endswith(".yaml") or path.endswith(".json"):
        projects = _load_yaml_config(path)
    else:
        raise ConfigError("Unsupported filed format: {}.  Value formats are "
                          "Python file (.py), YAML file (.yaml), or a "
                          "JSON file (.json).")

    # Check for conflicts
    project_names = map(
        lambda p: Projects.qualified_name(p.name, p.organization), projects)
    projects_repo = Projects()

    with projects_repo.transaction():
        existing_projects = projects_repo.all_named(*project_names)
        conflicts_found = len(existing_projects)

        if conflicts_found and import_strategy == ImportStrategy.abort:
            existing_project_names = [p.name for p in existing_projects]
            raise ProjectConflictError("The following projects already exist in "
                                       "your data file: " +
                                       ", ".join(existing_project_names))

        if conflicts_found and import_strategy == ImportStrategy.overwrite:
            projects_repo.delete(*existing_projects)

        if conflicts_found and import_strategy == ImportStrategy.merge:
            _do_merge(projects_repo, projects)
        else:
            for project in projects:
                projects_repo.save(project)


def _do_merge(project_repo, new_projects):
    for project in new_projects:
        log.debug("Merging project: {}", project.name)

        existing_project = project_repo.get(project.name,
                                            project.organization)
        if existing_project:
            existing_project.desc = project.desc
            for metric in filter(lambda m: not existing_project.metric(m.name),
                                 project.metrics):
                copied_metric = Metric(name=metric.name,
                                       units=metric.units,
                                       desc=metric.desc,
                                       value_range=metric.value_range,
                                       default_value=metric.default_value)
                existing_project.add_metric(copied_metric)
        else:
            # This is a new project, so just add it to the session
            log.debug("New project found in merge, adding it: {}", project.name)
            project_repo.save(project)


def _load_python_config(path):
    conf_mod = imp.load_source("__prj_config__", path)
    return conf_mod.configure()


def _load_yaml_config(path):
    with open(path, "r") as f:
        config = yaml.load(f)

    projects = []
    for project in config["projects"]:
        p = Project(name=project["name"],
                    desc=project.get("desc"))
        for metric in project["metrics"]:
            m = Metric(name=metric["name"],
                       units=getattr(units, metric["units"]),
                       desc=metric.get("desc"),
                       value_range=metric.get("value_range"),
                       default_value=metric.get("default_range"))
            p.add_metric(m)

        projects.append(p)

    return projects