"""
Unit tests for the ``maxify.main`` module.
"""

from io import StringIO
from threading import Thread

import pytest

from maxify.ui import MaxifyCmd


@pytest.fixture
def stdin():
    return StringIO()


@pytest.fixture
def stdout():
    return StringIO()


def test_exit(stdin, stdout):
    _run_cmd(stdin, stdout, "exit")
    assert stdout.getvalue() == "Maxify programmer time tracker client\n"


def test_quit(stdin, stdout):
    _run_cmd(stdin, stdout, "quit")
    assert stdout.getvalue() == "Maxify programmer time tracker client\n"


def _run_cmd(stdin, stdout, *commands):
    def cmd_thread():
        c = MaxifyCmd(stdin=stdin, stdout=stdout, use_color=False)
        c.prompt = ""
        c.use_rawinput = False
        c.completekey = None

        c.cmdloop()

    for command in commands:
        stdin.write(command + "\n")

    stdin.seek(0)

    t = Thread(target=cmd_thread, daemon=True)
    t.start()

    t.join(timeout=2)
    stdout.seek(0)


def test_projects(stdin, stdout, project, org1_project):
    _run_cmd(stdin,
             stdout,
             "projects",
             "exit")

    assert """
default
-------

 * test - Test Project

org1
----

 * org1/org1_project - Org1 Project

""" in stdout.getvalue()


def test_switch(stdin, stdout, project):
    _run_cmd(stdin,
             stdout,
             "switch " + project.name,
             "switch blah",
             "exit")

    output = stdout.getvalue()

    assert "Switched to project 'test'" in output
    assert "Error: No project found named 'blah'" in output