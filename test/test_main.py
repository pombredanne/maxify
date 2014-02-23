"""
Unit tests for the ``maxify.main`` module.
"""

import os
from io import StringIO
from threading import Thread
import re

import pytest

from maxify.main import MaxifyCmd
from maxify.config import import_config


@pytest.fixture
def stdin():
    return StringIO()


@pytest.fixture
def stdout():
    return StringIO()


@pytest.fixture
def cmd(stdin, stdout):
    c = MaxifyCmd(stdin=stdin, stdout=stdout, use_color=False)
    c.prompt = ""
    c.use_rawinput = False
    c.completekey = None
    return c


def test_exit(stdin, stdout, cmd):
    _run_cmd(stdin, cmd, "exit")
    assert stdout.getvalue() == cmd.intro + "\n"


def test_quit(stdin, stdout, cmd):
    _run_cmd(stdin, cmd, "quit")
    assert stdout.getvalue() == cmd.intro + "\n"


def _run_cmd(stdin, cmd, *commands):
    for command in commands:
        stdin.write(command + "\n")

    stdin.seek(0)

    t = Thread(target=cmd.cmdloop, daemon=True)
    t.start()

    t.join(timeout=2)

# TODO: These will be fixed after refactoring of data model access

# def test_project(stdin, stdout, cmd):
#     _run_cmd(stdin,
#              cmd,
#              "project test",
#              "project blah",
#              "exit")
#
#     output = re.split("\n+", stdout.getvalue())
#     assert "Switched to project 'Test Project'" in output
#     assert "Error: No project found named 'blah'" in output
#
#
# def test_projects(stdin, stdout, cmd):
#     _run_cmd(stdin,
#              cmd,
#              "project",
#              "exit")
#
#     output = re.split("\n+", stdout.getvalue())
#     assert "* Test Project (nickname: test) -> Test Project" in output
#     assert "* NEP (nickname: nep) -> NEP project" in output
#
#
# def test_print_project(stdin, stdout, cmd):
#     _run_cmd(stdin,
#              cmd,
#              "project test",
#              "print",
#              "exit")
#
#     output = re.split("\n+", stdout.getvalue())
#     assert "Project: Test Project" in output
#
#
# def test_create_task(stdin, stdout, cmd):
#     _run_cmd(stdin,
#              cmd,
#              "project test",
#              "task task_1")