"""
Unit tests for the ``maxify.config`` module.
"""
import pytest

from maxify.config import *
from maxify.metrics import *

from logbook import Logger

log = Logger("test_config")


@pytest.fixture(scope="module")
def test_dir():
    return os.path.dirname(__file__)


def test_load_python_config(test_dir):
    import_config(os.path.join(test_dir, "sample_conf.py"))
    _verify_config()


def test_load_python_yaml(test_dir):
    import_config(os.path.join(test_dir, "sample_conf.yaml"))
    _verify_config()


def test_load_conflict_abort(test_dir):
    import_config(os.path.join(test_dir, "sample_conf.py"))

    with pytest.raises(ProjectConflictError):
        import_config(os.path.join(test_dir, "sample_conf.yaml"),
                      import_strategy=ImportStrategy.abort)


def test_load_conflict_overwrite(test_dir):
    import_config(os.path.join(test_dir, "sample_conf.py"))

    project = Projects().get("test")

    assert project.desc == "Test Project"
    assert len(project.metrics) == 1

    import_config(os.path.join(test_dir, "sample_conf.yaml"),
                  import_strategy=ImportStrategy.overwrite)

    project = Projects().get("test")

    assert project.desc == "Test Project YAML"
    assert len(project.metrics) == 2

    assert len(Projects().all()) == 3


def test_load_conflict_merge(test_dir):

    log.info("Loading sample_conf.py")
    import_config(os.path.join(test_dir, "sample_conf.py"))

    import_config(os.path.join(test_dir, "sample_conf.yaml"),
                  import_strategy=ImportStrategy.merge)

    project = Projects().get("test")
    assert len(project.metrics) == 3


def test_no_path():
    with pytest.raises(ConfigError):
        import_config(None)

    with pytest.raises(ConfigError):
        import_config("blah")


def _verify_config():
    projects = Projects()
    project = projects.get("nep")

    assert project.desc == "NEP project"
    assert len(project.metrics) == 7
    print(project._metrics_map)
    assert project.metric("Story Points")
    assert project.metric("Story Points").metric_type == Number