"""
This module defines classes/types representing that data model utilized by
Maxify to represent projects, tasks, metrics, and data points.
"""

from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Numeric,
    DateTime
)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import ForeignKey

from maxify import config

Base = declarative_base()

#######################################
# Model types
#######################################


class ModelError(BaseException):
    pass


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    project = Column(String, index=True)
    name = Column(String(256))
    desc = Column(String, nullable=True)
    created = Column(DateTime)
    last_updated = Column(DateTime)

    data_points = relationship("DataPoint")

    def __init__(self,
                 project,
                 name,
                 desc=None):
        project = _to_name(project, config.Project)

        if not isinstance(project, str):
            raise ModelError("project argument must be either a string or a "
                             "Project instance.")

        self.project = project
        self.name = name
        self.desc = desc

        self.created = datetime.now()
        self.last_updated = self.created

        self._metrics = {}

    def _init_points_map(self):
        if not len(self._metrics) == len(self.data_points):
            self._points_map = {p.metric: p for p in self.data_points}

    def update_data_point(self, metric, value):
        self._init_points_map()

        if not metric.name in self._metrics:
            data_point = DataPoint(self.project,
                                   metric,
                                   value)
            self.data_points.append(data_point)
            self._metrics[metric.name] = data_point
        else:
            # TODO - going to probably change this to take a function instead,
            # like d3.js, to make an abitrary data transformation (so
            # things like +, -, reset, etc can be externalized.
            data_point = self._metrics[metric.name]
            data_point.value += value

        self.last_updated = datetime.now()

    def data_point(self, metric):
        self._init_points_map()

        return self._metrics.get(metric.name)

    def data_point_value(self, metric):
        data_point = self.data_point(metric)
        if not data_point:
            return None

        return data_point.value

    def __repr__(self):
        return "<Task: {0} ({1} Updated: {2}>".format(self.name,
                                                      self.created,
                                                      self.last_updated)


class DataPoint(Base):
    __tablename__ = "data_points"

    id = Column(Integer, primary_key=True)
    project = Column(String, index=True)
    metric = Column(String, index=True)

    str_value = Column(String, nullable=True)
    num_value = Column(Numeric, nullable=True)

    task_id = Column(Integer, ForeignKey("tasks.id"))

    def __init__(self,
                 project,
                 metric,
                 value=None):
        project = _to_name(project, config.Project)
        metric = _to_name(metric, config.Metric)

        if not isinstance(project, str):
            raise ModelError("project argument must be either a string or a "
                             "Project instance.")

        if not isinstance(metric, str):
            raise ModelError("metric argument must be either a string or a "
                             "Metric instance.")

        self.project = project
        self.metric = metric
        self.value = value

    @property
    def value(self):
        if hasattr(self, "str_value") and self.str_value:
            return self.str_value
        else:
            return self.num_value

    @value.setter
    def value(self, val):
        if isinstance(val, str):
            self.str_value = val
        else:
            self.num_value = val

    def __repr__(self):
        return "<DataPoint {0} {1}-{2}>".format(self.value,
                                                self.project,
                                                self.metric)


#######################################
# Utility functions
#######################################

def open_user_data(path, echo=False):
    engine = create_engine("sqlite:///" + path, echo=echo)
    Base.metadata.create_all(engine)
    Session = sessionmaker()
    Session.configure(bind=engine)
    return Session()


def _to_name(obj, type):
    if isinstance(obj, type):
        return getattr(obj, "name")
    else:
        return obj