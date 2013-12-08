"""
Module defines DSL/API for configuring a project via a Python.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation
import inspect
import imp
import re
import os

DEFAULT_PY_CONF = "conf.py"


class ConfigError(BaseException):
    """Type of error generadted due to a configuration error, such as defining
    invalid units or metrics.
    """
    pass


class ParsingError(BaseException):
    """Type of error generated due to a bad attempt at a data conversion.
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


class Unit(object):
    @staticmethod
    def parse(s):
        raise NotImplementedError("Method not implemented on base class")


class Int(Unit):
    @staticmethod
    def parse(s):
        try:
            return int(s)
        except ValueError:
            raise ParsingError("Invalid int expression: " + s)


class Float(Unit):
    @staticmethod
    def parse(s):
        try:
            return Decimal(s)
        except InvalidOperation:
            raise ParsingError("Invalid float expression: " + s)


class Duration(Unit):
    units = (
        ({"days", "day", "d"}, 86400),
        ({"hours", "hour", "hrs", "hr", "h"}, 3600),
        ({"minutes", "minute", "mins", "min", "m"}, 60),
        ({"seconds", "second", "secs", "sec", "s"}, 1)
    )

    expr_re = re.compile("(?:(?P<unit>[A-Za-z]+)\s*(?P<num>\d+\.?\d*))|"
                         "(?:(?P<num_alt>\d+\.?\d*)\s*(?P<unit_alt>[A-Za-z]+))")

    @classmethod
    def parse(cls, s):
        # First, attempt to parse it as a time format
        value = cls._try_parse_time_fmt(s)
        if value:
            return value

        value = Decimal(0)
        for match in cls.expr_re.finditer(s):
            num = match.group("num") if match.group("num") \
                else match.group("num_alt")
            unit = match.group("unit") if match.group("unit") \
                else match.group("unit_alt")

            found_units = [(u, m) for (u, m) in cls.units if unit in u]
            if not len(found_units):
                raise ParsingError("Invalid duration expression: " +
                                   match.group())
            _, multiplier = found_units[0]
            value += Decimal(num) * multiplier

        return value

    @staticmethod
    def _try_parse_time_fmt(s):
        dt = None
        try:
            dt = datetime.strptime(s, "%H:%M:%S")
        except BaseException:
            pass

        try:
            dt = datetime.strptime(s, "%H:%M")
        except BaseException:
            pass

        if dt:
            t = dt.time()
            return t.hour * 3600 + t.minute * 60 + t.second
        else:
            return None


class String(Unit):
    @staticmethod
    def parse(s):
        return s


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