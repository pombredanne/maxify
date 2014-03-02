"""
This module defines classes/types representing that data model utilized by
Maxify to represent projects, tasks, metrics, and data points.
"""

from datetime import datetime
from decimal import Decimal
import uuid

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Numeric,
    DateTime,
    Text
)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql.sqltypes import PickleType
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.pool import StaticPool

from maxify import units as model_units

Base = declarative_base()

#######################################
# Model types
#######################################


class ModelError(BaseException):
    pass


class DecimalType(TypeDecorator):
    impl = Text

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return self.impl
        else:
            return Numeric

    def process_bind_param(self, value, dialect):
        return str(value) if value is not None else None

    def process_result_value(self, value, dialect):
        if not value:
            return None

        return Decimal(value)


class UnitsType(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        return value.__name__

    def process_result_value(self, value, dialect):
        return getattr(model_units, value)


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses Postgresql's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value).hex
            else:
                return value.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(value)


class Project(Base):
    __tablename__ = "projects"

    #: String used to separate an organization from a name in a
    #: fully-qualified project name.  For instance, `scopetastic/maxify`
    org_separator = "/"

    id = Column(GUID, primary_key=True)
    name = Column(String(256), index=True, unique=True)
    organization = Column(String(100), index=True)
    desc = Column(String, nullable=True)

    metrics = relationship("Metric",
                           cascade="all, delete, delete-orphan",
                           backref="project")
    tasks = relationship("Task",
                         cascade="all, delete, delete-orphan",
                         backref="project")

    def __init__(self,
                 name,
                 organization=None,
                 desc=None,
                 metrics=[]):
        self.id = uuid.uuid4()
        self.name = name
        self.organization = organization
        self.desc = desc
        self._task_map = {}
        self._metrics_map = {}

        for metric in metrics:
            self.add_metric(metric)

    def unpack(self):
        self._task_map = {t.name: t for t in self.tasks}
        self._metrics_map = {m.name: m for m in self.metrics}
        for task in self.tasks:
            task.unpack()

    def add_metric(self, metric):
        self.metrics.append(metric)
        self._metrics_map[metric.name] = metric

    def metric(self, name):
        return self._metrics_map.get(name)

    def task(self, name):
        task = self._task_map.get(name)
        if not task:
            task = Task(self, name)
            self.tasks.append(task)
            self._task_map[name] = task

        return task

    @property
    def qualified_name(self):
        """The fully-qualified project name including organization.

            >>> project = Project("maxify", organization="scopetastic")
            >>> print(project.qualified_name)
            'scopetastic/maxify'

        :return: `str` containing fully-qualified name of the project.
        """
        if not self.organization:
            return self.name
        else:
            return self.organization + self.org_separator + self.name

    @classmethod
    def split_qualfied_name(cls, name):
        """Splits a fully-qualified project name into a tuple containing the
        organization and short name.

            >>> project = Project("maxify", organization="scopetastic")
            >>> Project.split_qualfied_name(project.qualified_name)
            ('scopetastic', 'maxify')

        :param name: The project name to split.

        :return: `tuple` in the form of (organization, name).  If organization
        is not specified in the original string, it will be set to ``None``.

        """
        if cls.org_separator not in name:
            return None, name

        index = name.find(cls.org_separator)
        organization = name[:index]
        name = name[index + 1:]

        return organization, name


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(GUID, primary_key=True)
    name = Column(String(256), index=True)
    units = Column(UnitsType)
    desc = Column(String, nullable=True)
    value_range = Column(PickleType, nullable=True)
    default_value = Column(DecimalType, nullable=True)

    project_id = Column(GUID, ForeignKey("projects.id",
                                         ondelete="cascade",
                                         onupdate="cascade"))

    data_points = relationship("DataPoint",
                               cascade="all, delete, delete-orphan",
                               backref="metric")

    def __init__(self,
                 name,
                 units,
                 desc=None,
                 value_range=None,
                 default_value=None):
        self.id = uuid.uuid4()
        self.name = name
        self.units = units
        self.desc = desc
        self.value_range = value_range
        self.default_value = default_value


class Task(Base):
    """Object representing a single measured task within a project.  Tasks
    contain 0 or more :class:`DataPoint` objects, one for each metric configured
    for the project.

    :param project: `str` or :class:`maxify.config.Project` object representing
        the project that this task belongs to.
    :param name: `str` containing the name of the task.
    :param desc: Optional `str` containing description of the task.

    """
    __tablename__ = "tasks"

    id = Column(GUID, primary_key=True)
    name = Column(String(256))
    desc = Column(String, nullable=True)
    created = Column(DateTime)
    last_updated = Column(DateTime)

    project_id = Column(GUID, ForeignKey("projects.id",
                                         ondelete="cascade",
                                         onupdate="cascade"))

    data_points = relationship("DataPoint",
                               cascade="all, delete, delete-orphan")

    def __init__(self,
                 project,
                 name):
        self.id = uuid.uuid4()
        self.project = project
        self.name = name

        self.created = datetime.now()
        self.last_updated = self.created

        self._points_map = {}
        self.update_data_points(*project.metrics)

    def unpack(self):
        self._points_map = {p.metric.id: p for p in self.data_points}

    def update_data_points(self, *args):
        for arg in args:
            if type(arg) is tuple:
                metric, value = arg
            else:
                metric = arg
                value = metric.default_value

            data_point = self._points_map.get(metric.id)
            if not data_point:
                data_point = DataPoint(self.project, metric, self)
                self.data_points.append(data_point)
                self._points_map[metric.id] = data_point

            data_point.value = value

    def data_point(self, metric):
        """Return the data point associated with the specified metric.

        :param metric: :class:`maxify.config.Metric` associated with the data
            point to return.

        :return The :class:`DataPoint` object associated with the specified
            Metric, or None if not found.

        """
        return self._points_map.get(metric.id)


class DataPoint(Base):
    """Object used to represent a data point for a :class:`maxify.config.Metric`
    associated with a single :class:`Task` object.

    :param project: :class:`maxify.config.Project`
    :param metric: :class:`maxify.config.Metric`.
    :param task: The parent :class:`Task` object.

    """

    __tablename__ = "data_points"

    id = Column(GUID, primary_key=True)

    metric_id = Column(GUID, ForeignKey("metrics.id",
                                        ondelete="cascade",
                                        onupdate="cascade"))
    task_id = Column(GUID, ForeignKey("tasks.id",
                                      ondelete="cascade",
                                      onupdate="cascade"))

    num_value = Column(DecimalType, nullable=True)

    def __init__(self,
                 project,
                 metric,
                 task):

        self.id = uuid.uuid4()
        self.project_id = project.name
        self.metric = metric
        self.metric_id = metric.name
        self.task_id = task.id

    @property
    def value(self):
        """The value of the data point.
        """
        return self.num_value


    @value.setter
    def value(self, val):
        val = self.metric.units.parse(val)

        if self.metric.value_range and not val in self.metric.value_range:
            print(self.metric.value_range)
            raise ModelError("Value {0} not in metric's valid "
                             "value range".format(val))

        self.num_value = val


#######################################
# Utility functions
#######################################


def open_user_data(path, echo=False, use_static_pool=False):
    """Opens the local SQLite data store containing task data for the user.

    :param path: The path to the SQLite database/data file.
    :param echo: Optional `bool` that if `True` will turn on echoing of
        SQL statements in SQLAlchemy.
    :param use_static_pool: Optional argument that indicates to this
        function to use SQLAlchemy's `StaticPool` pool class and to disable
        same thread checks for SQLite.  This is used only for unit testing
        where a second thread might be used for not blocking user I/O
        but all writes are still performed on the same thread.
    """
    url = "sqlite:///" + path
    kwargs = dict(echo=echo)
    if use_static_pool:
        kwargs["connect_args"] = dict(check_same_thread=False)
        kwargs["poolclass"] = StaticPool

    engine = create_engine(url, **kwargs)

    def on_connect(conn, record):
        conn.execute("pragma foreign_keys=ON")

    from sqlalchemy import event
    event.listen(engine, "connect", on_connect)

    engine.execute("pragma foreign_keys=ON")
    Base.metadata.create_all(engine)
    session = sessionmaker()
    session.configure(bind=engine)
    return session()
