"""
Module containing basic utilities and abstractions for the data storage layer
that serve as the basis for storage of metrics and projects.
"""
from datetime import timedelta

from decimal import Decimal
import uuid

from sqlalchemy import (
    create_engine,
    Numeric,
    Text
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import Float
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.pool import StaticPool

Base = declarative_base()

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


#######################################
# Type decorators
#######################################


class DecimalType(TypeDecorator):
    """Type decorator used for storage of Python decimal values.
    """
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


class IntervalType(TypeDecorator):
    """Type decorator used for storage of :class:`datetime.timedelta` objects
    as a number of seconds.

    This decorator is used instead of sqlalchemy's ``Interval`` type since
    this will allow us to use SQL aggregate functions, like SUM.

    """
    impl = Float

    def process_bind_param(self, value, dialect):
        return value.total_seconds() if value else None

    def process_result_value(self, value, dialect):
        if not value:
            return None

        return timedelta(seconds=value)


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