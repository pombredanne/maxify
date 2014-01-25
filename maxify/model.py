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
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
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
        self._points_map = None

    def _init_points_map(self):
        if not self._points_map:
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
    """Object used to represent a data point for a :class:`maxify.config.Metric`
    associated with a single :class:`Task` object.

    :param project: Either string containing name of the project that the
        data point belongs to, or a :class:`maxify.config.Project`.
    :param metric: Either string containing name of the metric that the data
        point is associated with, or a :class:`maxify.config.Metric`.
    :param value: Optional numeric or string value to set for the data point.

    """

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


class ProjectStore(object):
    """Object that provides access to tasks associated with a project
    defined by a :class:`maxify.config.Project` configuration object
    and its associated metrics.

    :param project_config: :class:`maxify.config.Project` config object
        defining configuration for the project and its metrics.
    :param db_session: SQLAlchemy session object generated by the
        `open_user_data` method and used for persisting task data.

    """

    def __init__(self, project_config, db_session):
        self.project_config = project_config
        self.db_session = db_session

    @property
    def project_id(self):
        """The ID of the project used in persisting tasks.

        """
        return self.project_config.name

    @property
    def tasks(self):
        """List of tasks for this project.

        """
        return self.db_session.query(Task) \
            .filter_by(project=self.project_id) \
            .all()

    def task(self, name):
        """Get the :class:`Task` with the specified name in this project.

        :return: The :class:`Task` object, or None if not found.
        """
        try:
            return self.db_session.query(Task) \
                .filter_by(project=self.project_id,
                           name=name).one()
        except NoResultFound:
            return None
        except MultipleResultsFound:
            return None

    def update_task(self, name, desc=None, metrics=None):
        """Update the :class:`Task` with the specified name.  If the task
        does not exist, it will be created.

        :param name: The name of the task to create/update.
        :param desc: Optional string description of the task.
        :param metrics: `List` of `tuples` in the form of `(metric, value)`,
            where `metric` is a :class:maxify.config.Metric object representing
            the metric to be updated/set, and `value` being a string or
            numberic value to assign to the data point associated with
            the metric.

        :return: The created/updated :class:`Task`.

        """
        task = self.task(name)
        if not task:
            task = Task(self.project_id, name, desc)

        self.db_session.add(task)
        for (metric, value) in metrics:
            task.update_data_point(metric, value)

        self.db_session.commit()

        return task


#######################################
# Utility functions
#######################################

def open_user_data(path, echo=False):
    """Opens the local SQLite data store containing task data for the user.

    :param path: The path to the SQLite database/data file.
    :param echo: Optional `bool` that if `True` will turn on echoing of
        SQL statements in SQLAlchemy.
    """
    engine = create_engine("sqlite:///" + path, echo=echo)
    Base.metadata.create_all(engine)
    Session = sessionmaker()
    Session.configure(bind=engine)
    return Session()


def _to_name(obj, obj_type):
    if isinstance(obj, obj_type):
        return getattr(obj, "name")
    else:
        return obj