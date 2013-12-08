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
        pass

    def do_project(self, line):
        """Switch to a project with the provided name."""
        self.current_project = Project.project(line.strip())
        if not self.current_project:
            self._error("No project found named '{0}'".format(line))
        else:
            self._success("Switched to project '{0}'".format(
                self.current_project.name))

    def do_task(self, line):
        """Create a task or edit an existing task."""
        pass

    def do_delete(self, line):
        """Delete the task with the specifed name."""
        pass

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

    def _print_task(self, line):
        print("Not implemented")


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
