"""
Module defines DSL/API for configuring a project via a Python.
"""

import inspect


class ConfigError(Exception):
    """Type of error generated due to a configuration error, such as defining
    invalid units or metrics.
    """
    pass


class Project(object):
    def __init__(self, name, desc, **kwargs):
        self.name = name
        self.desc = desc
        # Copy over any additional metadata/properties provided as keyword
        # arg
        for key in kwargs:
            setattr(self, key, kwargs[key])

        self.metrics = {}

    def add_metric(self,
               name,
               units,
               desc=None,
               range=None,
               default_value=None):
        if name in self.metrics:
            raise ConfigError("A metric named {0} already exists for this "
                              "project.")

        self.metrics[name] = Metric(name,
                                    units,
                                    desc=desc,
                                    range=range,
                                    default_value=default_value)

    def metric(self, name):
        return self.metrics[name]


class Metric(object):
    def __init__(self,
                 name,
                 units,
                 desc=None,
                 range=None,
                 default_value=None):
        if not inspect.isclass(units):
            raise ConfigError("Units specified must be a Unit class.")

        if not issubclass(units, Unit):
            raise ConfigError("A Metric's units must be a valid type of Unit.")

        self.name = name
        self.units = units
        self.desc = desc
        self.range = range
        self.default_value = default_value


class Unit(object):
    pass


class Int(Unit):
    pass


class Float(Unit):
    pass


class Duration(Unit):
    pass


class Enum(Unit):
    pass


class String(Unit):
    pass