"""
Unit tests for the ``maxify.config`` module.
"""
import pytest

from maxify.config import *
from maxify.model import Project
from maxify.units import *

from logbook import Logger

log = Logger("test_config")


@pytest.fixture(scope="module")
def test_dir():
    return os.path.dirname(__file__)


def test_load_python_config(test_dir,
                            db_session):
    import_config(db_session, os.path.join(test_dir, "sample_conf.py"))
    _verify_config(db_session)


def test_load_python_yaml(test_dir,
                          db_session):
    import_config(db_session, os.path.join(test_dir, "sample_conf.yaml"))
    _verify_config(db_session)


def test_load_conflict_abort(test_dir,
                             db_session):
    import_config(db_session, os.path.join(test_dir, "sample_conf.py"))

    with pytest.raises(ProjectConflictError):
        import_config(db_session,
                      os.path.join(test_dir, "sample_conf.yaml"),
                      import_strategy=ImportStrategy.abort)


def test_load_conflict_overwrite(test_dir,
                                 db_session):
    import_config(db_session, os.path.join(test_dir, "sample_conf.py"))

    project = db_session.query(Project).filter_by(name="Test Project").one()
    project.unpack()

    assert project.desc == "Test Project"
    assert len(project.metrics) == 1

    import_config(db_session,
                  os.path.join(test_dir, "sample_conf.yaml"),
                  import_strategy=ImportStrategy.overwrite)

    project = db_session.query(Project).filter_by(name="Test Project").one()
    project.unpack()

    assert project.desc == "Test Project YAML"
    assert len(project.metrics) == 2

    assert db_session.query(Project).count() == 3


def test_load_conflict_merge(test_dir,
                             db_session):

    log.info("Loading sample_conf.py")
    import_config(db_session, os.path.join(test_dir, "sample_conf.py"))

    import_config(db_session,
                  os.path.join(test_dir, "sample_conf.yaml"),
                  import_strategy=ImportStrategy.merge)

    project = db_session.query(Project).filter_by(name="Test Project").one()
    project.unpack()

    assert len(project.metrics) == 3


def test_no_path(db_session):
    with pytest.raises(ConfigError):
        import_config(db_session, None)

    with pytest.raises(ConfigError):
        import_config(db_session, "blah")


def _verify_config(db_session):
    project = db_session.query(Project).filter_by(name="NEP").one()
    project.unpack()

    assert project.desc == "NEP project"
    assert len(project.metrics) == 7
    assert project.metric("Story Points")
    assert project.metric("Story Points").units == Int