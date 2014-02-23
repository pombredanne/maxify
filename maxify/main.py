#!/usr/bin/env python

"""
Main module for maxify command line application.
"""

import argparse
import cmd
import shlex

import colorama
from maxify.units import ParsingError
from termcolor import colored
import logbook

from maxify.config import (
    import_config,
    ImportStrategy,
    ProjectConflictError,
    ConfigError
)
from maxify.repo import Repository, Projects
from maxify.log import enable_loggers

help_texts = {
    "projects": """Prints a list of all available projects.

""",
    "import": """Imports projects defined in a specified configuration file.

Configuration files can either by a YAML file or a Python module.

Example:

> import projects.yaml

""",
    "switch": """Switches to the project with the specified name.

Examples:

> switch sample1
> switch scopetastic/maxify

"""
}

class MaxifyCmd(cmd.Cmd):
    """Command interpreter used for accepting commands from the user to
    manage a Maxify project.

    """

    def __init__(self, stdin=None, stdout=None, use_color=True):
        cmd.Cmd.__init__(self, stdin=stdin, stdout=stdout)
        self.intro = "Maxify programmer time tracker client"
        self.prompt = "> "
        self.current_project = None
        self.use_color = use_color
        self.projects = Projects()
        self._generate_help_funcs()

    def _generate_help_funcs(self):
        for command in help_texts:
            self._generate_help_func(command)

    def _generate_help_func(self, command):
        func_name = "help_" + command

        def help_func():
            self._title("Help - " + command)
            self._print(help_texts[command])

        setattr(self, func_name, help_func)

    def cmdloop(self, project_name=None):
        if project_name:
            self._set_current_project(project_name)
            if self.current_project:
                self.intro = self.intro + \
                    "\n\n" + \
                    "Switched to project '{0}'".format(
                        self.current_project.name)
            else:
                self.intro = self.intro + \
                    "\n\nNo project found named '{0}'".format(project_name)

        cmd.Cmd.cmdloop(self)

    def _set_current_project(self, project_name):
        self.current_project = self.projects.get(project_name)

    def emptyline(self):
        """Handles an empty line (does nothing)."""
        pass

    # TODO: Keep this?
    def default(self, line):
        if self.current_project:
            task = self.current_project.task(line.strip())
        else:
            task = None

        if task:
            self._print_task(task)
            return

        cmd.Cmd.default(self, line)

    def do_switch(self, line):
        """Switch to a project with the provided name."""
        self._set_current_project(line.strip())

        if not self.current_project:
            self._error("No project found named '{0}'".format(line))
        else:
            self._success("Switched to project '{0}'".format(
                self.current_project.name))

    def do_projects(self, line):
        """Lists all projects current defined in the user's data file.
        """
        projects = self.projects.all()
        self._print("\n")

        if not len(projects):
            self._warning("No projects found")
            return

        orgs = [project.organization for project in projects]
        by_org = {org: filter(lambda p: p.organization == org, projects) for org in orgs}

        for org in sorted(orgs):
            if org:
                self._title(org)

            for project in by_org[org]:
                self._print_project_summary(project)

            self._print("\n")

    def _print_project_summary(self, project):
        project_str = " * {name} - {desc}".format(
            name=Projects.qualified_name(project.name, project.organization),
            desc=project.desc if project.desc else "No description provided")
        self._print(project_str)

    def do_import(self, line):
        """Import projects from a configuration file.

        """
        # First, attempt an import and abort if a conflict happens
        file_path = line.strip()
        try:
            projects = import_config(file_path, ImportStrategy.abort)
            conflict = False
        except ProjectConflictError:
            conflict = True
        except ConfigError as e:
            self._error(str(e))
            return

        if conflict:
            self._warning("Conflicts found between current projects and "
                          "projects defined in '{}'.".format(file_path))

            self._print("\nYou can select one of the following options for "
                        "continuing with the import:\n"
                        " - (A)bort -  Stops the import and makes no changes.\n"
                        " - (M)erge - Merges current projects with those "
                        "being imported.\n"
                        " - (R)eplace - Replaces current projects with the "
                        "ones being imported. Any existing conflicting "
                        "projects will be deleted along with their data.\n\n")

            response = input("What would you like to do?: ")

            if response == "M":
                self._print("Merging projects\n")
                projects = import_config(file_path, ImportStrategy.merge)
            elif response == "R":
                self._print("Replacing projects\n")
                projects = import_config(file_path, ImportStrategy.replace)
            else:
                self._print("Import aborted\n")
                projects = None

        if not projects:
            return

        self._print("\nThe following projects were imported:")
        for project in projects:
            self._print_project_summary(project)

        self._print("\n")

    def do_metrics(self, line):
        """Print out metrics available for the current project."""
        if not self.current_project:
            self._error("Please select a project first using the 'project' "
                        "command")
            return

        for metric_name in sorted(self.current_project.metrics):
            m = self.current_project.metrics[metric_name]
            if m.desc:
                self._print("* {0} ({1}) -> {2}".format(metric_name,
                                                        m.units.display_name(),
                                                        m.desc))
            else:
                self._print("* {0} ({1})".format(metric_name,
                                                 m.units.display_name()))

        self._print("")

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
                        "Usage: task [TASK_NAME]")
            return

        tokens = shlex.split(line)
        task_name = tokens[0]
        args = tokens[1:]

        if len(args):
            success = self._update_task(task_name, args)
        else:
            success = self._update_task_interactive(task_name)

        if success:
            self._success("Task updated")

    def _update_task_interactive(self, task_name):
        return False

    def _update_task(self, task_name, args):
        metrics = []
        for i in range(0, len(args), 2):
            metric_name = args[i]
            value_str = args[i + 1]
            metric = self._get_metric(metric_name)
            if not metric:
                self._error("Invalid metric: " + metric_name)
                return

            try:
                value = metric.units.parse(value_str)
            except ParsingError as e:
                self._error(str(e))
                return

            metrics.append((metric, value))

        self.current_project.update_task(task_name, metrics=metrics)

        return True

    def _get_metric(self, metric_name):
        # First, try to use the string as is:
        metric = self.current_project.metric(metric_name)
        if metric:
            return metric

        metric_name = metric_name.replace("_", " ").title()
        return self.current_project.metric(metric_name)

    def _print_task(self, task):
        output = ["Created: " + str(task.created)]
        output.append("Last Updated: " + str(task.last_updated))
        output.append("\n")
        for data_point in task.data_points:
            output.append(" {0} -> {1}".format(data_point.metric,
                                               data_point.value))

        self._print("\n".join(output) + "\n")

    ########################################
    # Utility methods
    ########################################

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
    parser = argparse.ArgumentParser(description="Maxify programmer time "
                                                 "tracker client")
    parser.add_argument("-p",
                        "--project",
                        help="Name of project to start tracking time against "
                             "once the client starts. For a project belonging "
                             "to a particular organization, prefix the name "
                             "with the organization, like: scopetastic/maxify.")
    parser.add_argument("-f",
                        "--data-file",
                        default="maxify.db",
                        help="Path to Maxify data file. By default, this is "
                             "'maxify.db' in the current directory.")

    parser.add_argument("-x",
                        "--debug",
                        action="store_true",
                        help="Print debugging statements during execution.")

    args = parser.parse_args()

    if args.debug:
        enable_loggers()

    colorama.init()
    Repository.init(args.data_file)

    interpreter = MaxifyCmd()
    interpreter.cmdloop(args.project)


if __name__ == "__main__":
    main()
