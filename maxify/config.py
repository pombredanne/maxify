"""
Module defines DSL/API for configuring a project via a Python.
"""

import inspect
import imp
import os

from maxify.units import Unit

DEFAULT_PY_CONF = "conf.py"


class ConfigError(BaseException):
    """Type of error generadted due to a configuration error, such as defining
    invalid units or metrics.
    """
    pass


class Project(object):
    projects = {}
    project_nicknames = {}

    def __init__(self, name, desc=None, nickname=None, **kwargs):
        self.name = name
        self.desc = desc
        self.nickname = nickname
        # Copy over any additional metadata/properties provided as keyword
        # arg
        for key in kwargs:
            setattr(self, key, kwargs[key])

        self.metrics = {}

        self.register_project(self)

    @classmethod
    def register_project(cls, project):
        if project.name in cls.projects:
            print("Warning: project named {0} already registered.".format(
                project.name
            ))
        cls.projects[project.name] = project

        if project.nickname in cls.project_nicknames:
            print("Warning: project nickname {0} already registered.".format(
                project.nickname
            ))
        cls.project_nicknames[project.nickname] = project

    @classmethod
    def project(cls, name):
        if name in cls.projects:
            return cls.projects[name]

        if name in cls.project_nicknames:
            return cls.project_nicknames[name]

        return None

    def add_metric(self,
                   name,
                   units,
                   desc=None,
                   value_range=None,
                   default_value=None):
        if name in self.metrics:
            raise ConfigError("A metric named {0} already exists for this "
                              "project.")

        self.metrics[name] = Metric(name,
                                    units,
                                    desc=desc,
                                    value_range=value_range,
                                    default_value=default_value)

    def metric(self, name):
        return self.metrics[name]


class Metric(object):
    def __init__(self,
                 name,
                 units,
                 desc=None,
                 value_range=None,
                 default_value=None):
        if not inspect.isclass(units):
            raise ConfigError("Units specified must be a Unit class.")

        if not issubclass(units, Unit):
            raise ConfigError("A Metric's units must be a valid type of Unit.")

        self.name = name
        self.units = units
        self.desc = desc
        self.value_range = value_range
        self.default_value = default_value


def load_config(path=None):
    if not path:
        if os.path.exists(DEFAULT_PY_CONF):
            path = DEFAULT_PY_CONF

    if not path:
        raise ConfigError("No configuration file specified or found in "
                          "current working directory.")

    # Try to load as a python module first
    if _load_python_config(path):
        return

    raise ConfigError("No valid config file loaded.")


def _load_python_config(path):
    try:
        conf_mod = imp.load_source("__prj_config__", path)
        return conf_mod
    except BaseException:
        return None