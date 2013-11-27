"""
This module defines classes/types representing that data model utilized by
Maxify to represent projects, tasks, metrics, and data points.
"""

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Enum,
    PickleType
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

#######################################
# Model types
#######################################


class Units(object):
    DURATION = 'duration'
    INTEGER = 'integer'
    DECIMAL = 'range'

    values = (DURATION, INTEGER, DECIMAL)


class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String(256), index=True)
    desc = Column(String(512))




class Metric(Base):
    __tablename__ = 'metrics'

    id = Column(Integer, primary_key=True)
    name = Column(String(256))
    desc = Column(String(512))
    type = Column(Enum(Units.values))
    data = Column(PickleType)


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    name = Column(String(512), index=True)
    created = Column(DateTime)
    last_update = Column(DateTime)
    metric_map = Column(PickleType)


#######################################
# Utility functions
#######################################

def open_user_data(path, echo=False):
    engine = create_engine('sqlite:///' + path, echo=echo)


