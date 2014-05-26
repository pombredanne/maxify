"""
Module defining metrics for a project and the different types of data that
can be stored in a metric.
"""

from datetime import datetime
import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.schema import PrimaryKeyConstraint
from sqlalchemy.sql.sqltypes import PickleType
from sqlalchemy.types import TypeDecorator

from maxify.data import (
    Base,
    GUID,
    DecimalType,
    IntervalType
)

#######################################
# Type decorators
#######################################


class MetricType(TypeDecorator):
    """Type decorator that allows for storage of the type of a metric based
    on the class name of the metric (for instance, Integer, Float, etc.)
    """

    impl = Text

    def process_bind_param(self, value, dialect):
        return value.__name__

    def process_result_value(self, value, dialect):
        for metric_type in filter(lambda m: m.__name__ == value, metric_types):
            return metric_type

#######################################
# Metrics
#######################################


class Metric(Base):
    """Class representing an individual metric for a project.
    """

    __tablename__ = "metrics"

    id = Column(GUID, primary_key=True)
    name = Column(String(256), index=True)
    metric_type = Column(MetricType)
    desc = Column(String, nullable=True)
    value_range = Column(PickleType, nullable=True)
    default_value = Column(DecimalType, nullable=True)

    project_id = Column(GUID,
                        ForeignKey("projects.id",
                                   ondelete="cascade",
                                   onupdate="cascade"),
                        index=True)

    def __init__(self,
                 name,
                 metric_type,
                 project,
                 desc=None,
                 value_range=None,
                 default_value=None):
        self.id = uuid.uuid4()
        self.name = name

        if not issubclass(metric_type, MetricData):
            raise TypeError("metric_type needs to be a subclass of MetricData")
        self.metric_type = metric_type

        self.project_id = project.id
        self.desc = desc
        self.value_range = value_range
        self.default_value = default_value


#######################################
# Metric data types
#######################################


class MetricData(object):
    """Mixin for metrics data that provides the bare-minimum set of properties
    for a data value, such as the ID of its parent metric, its value, and
    the timestamp of when the value was created/stored.

    :param metric: The :class:`maxify.metrics.Metric` that is the parent
        of this datum.
    :param task: The :class:`maxify.projects.Task` that this datum belongs
        to.

    """

    def __init__(self, metric, task):
        self.timestamp = datetime.now()
        self.metric_id = metric.id
        self.task_id = task.id

    @declared_attr
    def metric_id(self):
        """Column used to store reference to the metric that this datum is
        being measured for.
        """
        return Column(GUID,
                      ForeignKey("metrics.id",
                                 ondelete="cascade",
                                 onupdate="cascade"),
                      index=True)

    @declared_attr
    def task_id(self):
        """Column used to store reference to the task that the data value
        belongs to.
        """
        return Column(GUID,
                      ForeignKey("tasks.id",
                                 ondelete="cascade",
                                 onupdate="cascade"),
                      index=True)

    @declared_attr
    def timestamp(self):
        """Column providing the time the entry was created for the data value.
        """
        return Column(DateTime)


class Number(Base, MetricData):
    """Scalar, single-value metric data type that stores a numeric value (both
    integer and floating point, with full precision).

    :param metric: The :class:`maxify.metrics.Metric` that is the parent
        of this datum.
    :param task: The :class:`maxify.projects.Task` that this datum belongs
        to.
    :param value: The decimal value to assign to this datum.

    """

    __tablename__ = "metrics_data_numbers"

    #: The value of the datum as a :class:`decimal.Decimal`
    value = Column(DecimalType)

    # For numbers, since there is only a single value, the primary key should
    # be the combination of metric id and task id (forcing only a single value
    # that can be created).
    __table_args__ = (
        PrimaryKeyConstraint("metric_id", "task_id"),
        dict()
    )

    def __init__(self, metric, task, value):
        MetricData.__init__(self, metric, task)
        self.value = value

    @staticmethod
    def total(metric, task, session):
        """Returns the total value for the metric belonging to the specified
        task.  For a Number, this is a single, scalar value.

        :param metric: The :class:`maxify.metrics.Metric` that the duration
            is being measured for.
        :param task: The :class:`maxify.projects.Task` that the duration is
            being measured for.
        :param session: The sqlalchemy database session used to query the
            datastore.

        :return: The total value of the metric.
        """
        return session.query(Number.value)\
            .filter_by(metric_id=metric.id, task_id=task.id).scalar()


class Duration(Base, MetricData):
    """Histogram-style metric data type that represents a time duration or
    delta.  Unlike :class:`maxify.metrics.Number`:, durations are cumulative,
    and each duration entry is stored individually in order to provide a
    histogram of values over time.

    :param metric: The :class:`maxify.metrics.Metric` that is the parent
        of this datum.
    :param task: The :class:`maxify.projects.Task` that this datum belongs
        to.
    :param value: :class:`datetime.timedelta` value corresponding to the
        duration for this individual datum.

    """

    __tablename__ = "metrics_data_durations"

    #: Column uniquely identifying an individual datum in a duration
    #: histogram.
    id = Column(GUID, index=True)

    #: Value of the datum, represented by a :class:`datetime.timedelta`.
    value = Column(IntervalType)

    # For durations, since we can have multiple histogram values that
    # aggregate into a single duration value, use the id column as an
    # additional part of the primary key.
    __table_args__ = (
        PrimaryKeyConstraint("metric_id", "task_id", "id"),
        dict()
    )

    def __init__(self, metric, task,  value):
        MetricData.__init__(self, metric, task)
        self.id = uuid.uuid4()
        self.value = value

    @staticmethod
    def total(metric, task, session):
        """Returns the total value for a duration metric belonging to the
        specified task.

        :param metric: The :class:`maxify.metrics.Metric` that the duration
            is being measured for.
        :param task: The :class:`maxify.projects.Task` that the duration is
            being measured for.
        :param session: The sqlalchemy database session used to query the
            datastore.

        :return: The total duration as a :class:`datetime.timedelta`.

        """
        return session.query(func.sum(Duration.value).label("total"))\
            .filter_by(metric_id=metric.id, task_id=task.id).scalar()


#: List of different types of metrics that can be created/stored in a project.
metric_types = [
    Number,
    Duration
]