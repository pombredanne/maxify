"""Module defining constructs for projects and tasks
"""

from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey

from maxify.data import (
    Base,
    GUID
)
from maxify.metrics import Metric, Number, Duration


class Project(Base):
    """Class representing an individual project used to record metrics.

    A project is comprised of one or more tasks, which are in turn used to
    record values against.

    :param name: The unique name of the project
    :param organization: String containing name of an organization that the
        project belongs to.
    :param desc: Optional description of the project.
    :param metrics: List of :class:`maxify.metrics.Metric` objects defining
        metrics that can be record against tasks in this project.

    """
    __tablename__ = "projects"

    #: String used to separate an organization from a name in a
    #: fully-qualified project name.  For instance, `scopetastic/maxify`
    org_separator = "/"

    id = Column(GUID, primary_key=True)
    name = Column(String(256), index=True, unique=True)
    organization = Column(String(100), index=True)
    desc = Column(String, nullable=True)

    metrics = relationship(Metric,
                           cascade="all, delete, delete-orphan")
    tasks = relationship("Task",
                         cascade="all, delete, delete-orphan")

    def __init__(self,
                 name,
                 organization=None,
                 desc=None):
        self.id = uuid.uuid4()
        self.name = name
        self.organization = organization
        self.desc = desc
        self._task_map = {}
        self._metrics_map = {}

    def unpack(self):
        self._task_map = {t.name: t for t in self.tasks}
        self._metrics_map = {m.name: m for m in self.metrics}

    def add_metric(self,
                   name,
                   metric_type,
                   desc=None,
                   value_range=None,
                   default_value=None):
        """Adds a new metric to the current project with the specified
        properties.

        :param name: The name of the metric.  This will be unique to the
            project.
        :param metric_type: :class:`maxify.metrics.MetricData` subclass
            type representing the type of metric being added (for instance,
            a :class:`maxify.metrics.Duration`).
        :param desc: Optional :class:`string` containing a description of the
            metric.
        :param value_range: Optional :class:`list` or :class:`set` defining a
            set of valid values that can be assigned to this metric.  For
            instance, if you wanted to limit the metric to only
            ``[1, 2, 3, 4, 5]``.
        :param default_value: Optional default value for the metric.  If the
            user does not provide a value, this value will be assigned to
            the metric instead.

        :return: The current project.

        """
        metric = Metric(name,
                        metric_type,
                        project=self,
                        desc=desc,
                        value_range=value_range,
                        default_value=default_value)
        self.metrics.append(metric)
        self._metrics_map[metric.name] = metric
        return self

    def metric(self, name):
        """Returns the metric with the specified name.  Additionally, this
        method will attempt to find a metric by name using some different
        naming convention patterns in addition to exact name.

        Examples (for metric "Compile Time"):

            >>> project.metric("Compile Time")
            >>> project.metric("compile time")
            >>> project.metric("compile_time")

        :param name: The name of the metric.  The method will attempt
            to find a metric with a name that matches either the exact name,
            the name in a case-insensitive manner, or the name in a
            case-insensitive manner with spaces replaced by underscores.

        :return: The :class:`maxify.metrics.Metric` with the specified name
            in this project, or ``None`` if it does not exist.

        """
        metric = self._metrics_map.get(name)
        if metric:
            return metric

        name_lower = name.lower().replace("_", " ")
        for metric_name in self._metrics_map:
            if name_lower == metric_name.lower():
                return self._metrics_map[metric_name]

        return None

    def task(self, name):
        """Returns the task in the current project with the specified name.  If
        the task does not exist, it will be created.

        :param name: The unique name of the task.

        :return: The :class:`maxify.projects.Task` with the specified name
            in this project.  If the task does not exist, it will be
            created.

        """
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


class Task(Base):
    """Object representing a single measured task within a project.  Tasks
    contain 0 or more :class:`DataPoint` objects, one for each metric configured
    for the project.

    :param project: `str` or :class:`maxify.config.Project` object representing
        the project that this task belongs to.
    :param name: `str` containing the name of the task.

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

    numeric_values = relationship(Number,
                                  cascade="all, delete, delete-orphan")
    duration_values = relationship(Duration,
                                   cascade="all, delete, delete-orphan")

    def __init__(self,
                 project,
                 name):
        self.id = uuid.uuid4()
        self.project_id = project.id
        self.name = name

        self.created = datetime.now()
        self.last_updated = self.created

        self._metrics = {}

    def record(self, metric, value):
        """Records a metric's value for this task.

        :param metric: The :class:`maxify.metrics.Metric` to record a value
            for.
        :param value: The value to assign/record for the metric for this task.
        """
        if metric.metric_type == Number:
            self._record_number(metric, value)
        else:
            self.duration_values.append(Duration(metric, self, value))

    def _record_number(self, metric, value):
        existing = [val for val in self.numeric_values
                    if val.metric_id == metric.id]
        if len(existing):
            existing[0].value = value
        else:
            self.numeric_values.append(Number(metric, self, value))

    def value(self, metric):
        """Returns the total value for the metric in the current task.

        :param metric: The :class:`maxify.metrics.Metric` to get a total value
            for.

        :return: The total value of the specified metric.

        """
        data_points = self.histogram(metric)
        if metric.metric_type is Duration:
            start = timedelta()
        else:
            start = Decimal(0)

        return sum([dp.value for dp in data_points], start)

    def histogram(self, metric):
        """Returns a histogram of recorded values for the specified metric as
        a list of :class:`maxify.metrics.MetricData` objects.

        :param metric: The :class:`maxify.metrics.Metric` to get histogram
            values for.

        :return: :class:`list` of values for the specified metric.

        """
        if metric.metric_type is Duration:
            collection = self.duration_values
        else:
            collection = self.numeric_values

        return filter(lambda d: d.metric_id == metric.id, collection)
