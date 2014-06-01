"""
Module defines import utility for importing project configuration from
a file into the user's data store.

"""

import os
import runpy

from enum import Enum, unique

import yaml

from maxify.projects import Project
from maxify.metrics import metric_types
from maxify.repo import Projects
from maxify.log import Logger

log = Logger("config")

#: Constant defining name of key in config defining projects to import.
PROJECTS_KEY = "projects"


class ConfigError(BaseException):
    """Type of error generated due to a configuration error, such as defining
    invalid units or metrics.
    """
    pass


class ProjectConflictError(BaseException):
    """Type of error generated due to a conflict between an existing project
    and one trying to be imported.
    """
    pass


@unique
class ImportStrategy(Enum):
    """Enumeration of different strategies that can be used to import projects
    into the current data store.
    """
    #: Strategy that aborts the operation when a conflict is detected.
    abort = "abort"

    #: Strategy that will attempt to merge conflict projects into a single
    #: project.
    merge = "merge"

    #: Strategy that will overwrite one project with another if a duplicate
    #: is found in a configuration that is being imported.
    overwrite = "overwrite"


def import_config(path, import_strategy=ImportStrategy.abort):
    """Load project and metric configuration from the file specified and
    import into user's data file.

    :param path: `str` containing path to the configuration file.
    :param import_strategy: :class:`ImportStrategy` enum value indicating the
        import strategy to use in case a conflict is detected.

    :returns: List of projects that were imported

    :raise `ConfigError` Raised if invalid configuration file is found.

    """
    log.info("Attempting configuration import. Path: {} Stategy: {}",
             path,
             import_strategy)

    if not path:
        raise ConfigError("A path must be provided to import from.")

    if not os.path.exists(path):
        raise ConfigError("File {} does not exist".format(path))

    # Load projects from file
    if path.endswith(".py"):
        projects = _load_python_config(path)
    elif path.endswith(".yaml") or path.endswith(".json"):
        projects = _load_yaml_config(path)
    else:
        raise ConfigError("Unsupported filed format: {}.  Value formats are "
                          "Python file (.py), YAML file (.yaml), or a "
                          "JSON file (.json).")

    # For python config, allow a single return value instead of a collection.
    if isinstance(projects, Project):
        projects = [projects]

    # Check for conflicts
    project_names = [p.qualified_name for p in projects]
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

    return projects


def _do_merge(project_repo, new_projects):
    for project in new_projects:
        log.debug("Merging project: {}", project.name)

        existing_prj = project_repo.get(project.name,
                                        project.organization)
        if existing_prj:
            existing_prj.desc = project.desc
            for metric in project.metrics:
                existing_metric = existing_prj.metric(metric.name)
                if not existing_metric:
                    existing_prj.add_metric(name=metric.name,
                                            metric_type=metric.metric_type,
                                            desc=metric.desc,
                                            value_range=metric.value_range,
                                            default_value=metric.default_value)
                elif existing_metric.metric_type == metric.metric_type:
                    existing_metric.name = metric.name
                    existing_metric.desc = metric.desc
                    existing_metric.value_range = metric.value_range
                    existing_metric.default_value = metric.default_value
                else:
                    log.warn("Cannot merge metric {} because new unit is "
                             "different from existing unit type and this "
                             "would cause data loss.", metric.name)
        else:
            # This is a new project, so just add it to the session
            log.debug("New project found in merge, adding it: {}", project.name)
            project_repo.save(project)


def _load_python_config(path):
    config_globals = runpy.run_path(path)
    if not PROJECTS_KEY in config_globals:
        raise ConfigError("{} must contain a `projects` variable defining "
                          "either a list of Projects or a single Project."
                          .format(path))

    return config_globals[PROJECTS_KEY]


def _load_yaml_config(path):
    with open(path, "r") as f:
        config = yaml.load(f)

    projects = []
    for project in config[PROJECTS_KEY]:
        p = Project(name=project["name"],
                    organization=project.get("organization"),
                    desc=project.get("desc"))
        for metric in project["metrics"]:
            metric_type = [m for m in metric_types
                           if m.__name__ == metric["metric_type"]]
            if not len(metric_type):
                raise ConfigError("No metric type defined named " +
                                  metric["metric_type"])

            p.add_metric(name=metric["name"],
                         metric_type=metric_type[0],
                         desc=metric.get("desc"),
                         value_range=metric.get("value_range"),
                         default_value=metric.get("default_value"))

        projects.append(p)

    return projects