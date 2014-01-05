#!/usr/bin/env python

"""
Main module for maxify command line application.
"""

import cmd
import sys
from contextlib import contextmanager

import colorama
from termcolor import cprint

from maxify.config import load_config, Project


class MaxifyCmd(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.intro = "Maxify programmer time tracker client"
        self.prompt = "> "
        self.current_project = None

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
        sys.exit(0)

    def do_quit(self, line):
        """Exit the application."""
        self.do_exit(line)

    def _print_project(self):
        p = self.current_project
        # TODO - More content will come later
        print("Project: " + p.name)

    @classmethod
    def _print_projects(cls):
        cls._title("Projects")
        for project in Project.projects():
            print("* {0} (nickname: {1}) -> {2}".format(project.name,
                                                        project.nickname,
                                                        project.desc))
        print()

    @staticmethod
    def _print_task(line):
        print("Not implemented")

    @staticmethod
    def _title(line):
        print("\n" + line)
        print("-" * min(len(line), 80), "\n")

    @staticmethod
    def _success(msg):
        cprint(msg, 'green')
        print()

    @staticmethod
    def _warning(msg):
        cprint("Warning: " + msg, "yellow")
        print()

    @staticmethod
    def _error(msg):
        cprint("Error: " + msg, "red")
        print()


def main():
    colorama.init()
    load_config()

    interpreter = MaxifyCmd()
    interpreter.cmdloop()


if __name__ == "__main__":
    main()
