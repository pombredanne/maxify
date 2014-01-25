#!/usr/bin/env python

"""
Main module for maxify command line application.
"""

import cmd
import re
import shlex

import colorama
from termcolor import colored

from maxify.config import load_config, Project


class MaxifyCmd(cmd.Cmd):
    """Command interpreter used for accepting commands from the user to
    manage a Maxify project.

    """

    # Regex to parse name of task from task command line
    _task_name_re = re.compile('^(?:"(?P<task0>[\w\s]+)"|'
                               '\'(?P<task1>[\w\s]+)\'|'
                               '(?P<task2>\w+)\s*)')

    def __init__(self, stdin=None, stdout=None, use_color=True):
        cmd.Cmd.__init__(self, stdin=stdin, stdout=stdout)
        self.intro = "Maxify programmer time tracker client"
        self.prompt = "> "
        self.current_project = None
        self.use_color = use_color

    def emptyline(self):
        """Handles an empty line (does nothing)."""
        pass

    def do_project(self, line):
        """Switch to a project with the provided name."""
        line = line.strip()
        if not line:
            self._print_projects()
            return

        self.current_project = Project.project(line)
        if not self.current_project:
            self._error("No project found named '{0}'".format(line))
        else:
            self._success("Switched to project '{0}'".format(
                self.current_project.name))

    def do_print(self, line):
        """Print information on an existing task or project."""
        if not line:
            self._print_project()
        else:
            self._print_task(line)

    def do_exit(self, line):
        """Exit the application."""
        return True

    def do_quit(self, line):
        """Exit the application."""
        return True

    def do_task(self, line):
        """Create a task or edit an existing task."""
        line = line.strip()
        if not line:
            self._error("You must specify a task to create or update.\n"
                        " Usage: task [TASK_NAME]")

        # Extract task name from command line
        task_name = self._get_task_name(line)

    @classmethod
    def _get_task_name(cls, line):
        match = cls._task_name_re.match(line)
        if not match:
            return None

        return filter(lambda m: m is not None, match.groups())[0]

    def _print_project(self):
        p = self.current_project
        # TODO - More content will come later
        self._print("Project: " + p.name)

    def _print_projects(self):
        self._title("Projects")
        for project in Project.projects():
            self._print("* {0} (nickname: {1}) -> {2}".format(project.name,
                                                              project.nickname,
                                                              project.desc))
        self._print()

    def _print_task(self, line):
        self._print("Not implemented")

    def _title(self, line):
        self._print("\n" + line)
        self._print("-" * min(len(line), 80) + "\n")

    def _success(self, msg):
        self._print(msg, 'green')
        print()

    def _warning(self, msg):
        self._print("Warning: " + msg, "yellow")
        print()

    def _error(self, msg):
        self._print("Error: " + msg, "red")
        print()

    def _print(self, msg=None, color=None):
        if msg and color and self.use_color:
            msg = colored(msg, color)

        print(msg, file=self.stdout)


def main():
    colorama.init()
    load_config()

    interpreter = MaxifyCmd()
    interpreter.cmdloop()


if __name__ == "__main__":
    main()
