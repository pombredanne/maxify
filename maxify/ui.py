"""
Module defining user interface for the application.
"""

import cmd
import fnmatch
from io import StringIO
import shlex

from maxify.metrics import ParsingError, Duration
from termcolor import colored

from maxify.config import (
    import_config,
    ImportStrategy,
    ProjectConflictError,
    ConfigError
)
from maxify.repo import Projects, Tasks
from maxify.stopwatch import StopWatch
from maxify.utils import ArgumentParser, cbreak


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

""",
    "metrics": """Displays available metrics for tasks contained in the current\
 project.

Example:

    > metrics

""",
    "tasks": """List all tasks stored in the current project, and optionally
print details about each one.

Usage:

    > tasks [--details] [PATTERN]

The tasks command accepts the following arguments:

--details - Flag used to print out details on each task.
PATTERN   - Optional name pattern to use for only displaying a subset of tasks.
            The name pattern is a glob pattern.

Examples:

    > tasks
    > tasks --details
    > tasks --details maxify-1*

""",
    "task": """Create or update a task associated with the current project.

Tasks can be created or updated either in interactive or non-interactive mode.

Examples (non-interactive):

    > task maxify-1 compile_time 2hrs research_time 1hr
    > task maxify-1 "debug time" 20mins

Example (interactive):

    > task maxify-1
    Compile Time: 2 hrs
    Research Time: 1 hr
    Debug Time: 20 mins
    ...

"""
}


class MaxifyCmd(cmd.Cmd):
    """Command interpreter used for accepting commands from the user to
    manage a Maxify project.

    """

    _stopwatch_status_colors = {
        StopWatch.STATUS_RUNNING: "green",
        StopWatch.STATUS_PAUSED: "yellow",
        StopWatch.STATUS_RESET: "magenta",
        StopWatch.STATUS_STOPPED: "white"
    }

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

    def cmdloop(self, args=None):
        if args and args.project:
            self._set_current_project(args.project)
            if self.current_project:
                self.intro = self.intro + \
                             "\n\n" + \
                             "Switched to project '{0}'\n".format(args.project)
            else:
                self.intro = self.intro + \
                             "\n\nNo project found named '{0}'\n".format(args.project)

        if args and args.command and len(args.command) > 0:
            stdin = StringIO()
            self.stdin = stdin
            self.prompt = ""
            self.use_rawinput = False
            stdin.write(" ".join(args.command) + "\nexit\n")
            stdin.seek(0)

        try:
            cmd.Cmd.cmdloop(self)
        except KeyboardInterrupt:
            self._print("\nExiting\n")
            return

    def _set_current_project(self, project_name):
        self.current_project = self.projects.get(project_name)

    def emptyline(self):
        """Handles an empty line (does nothing)."""
        pass

    ########################################
    # Command - quit/exit
    ########################################

    def do_exit(self, line):
        """Exit the application."""
        return True

    def do_quit(self, line):
        """Exit the application."""
        return True

    ########################################
    # Command - switch
    ########################################

    def do_switch(self, line):
        """Switch to a project with the provided name."""
        self._set_current_project(line.strip())

        if not self.current_project:
            self._error("No project found named '{0}'".format(line))
        else:
            self._success("Switched to project '{0}'".format(
                self.current_project.name))

    def complete_switch(self, text, line, beginx, endidx):
        start_index = len("switch ")
        if beginx == start_index:
            return self.projects.matching_name(text)

        # If beginning index not immediately after command keyword, then
        # readline found a organization delimiter, so handle it correctly
        # in search for matches, then strip it out of returned results for
        # readline tokenized completion logic.
        organization = line[start_index:beginx]
        partial_name = organization + text
        matches = self.projects.matching_name(partial_name)
        return [m.replace(organization, "") for m in matches]

    ########################################
    # Command - projects
    ########################################

    def do_projects(self, line):
        """Lists all projects current defined in the user's data file.
        """
        projects = self.projects.all()

        if not len(projects):
            self._print("\nNo projects found\n")
            return

        orgs = {project.organization for project in projects}
        by_org = {org: [p for p in projects if p.organization == org]
                  for org in orgs}

        for org in sorted(orgs, key=lambda o: o if o is not None else ""):
            if org:
                self._title(org)
            else:
                self._title("default")

            for project in by_org[org]:
                self._print_project_summary(project)

        self._print()

    def _print_project_summary(self, project):
        project_str = " * {name} - {desc}".format(
            name=project.qualified_name,
            desc=project.desc if project.desc else "No description provided")
        self._print(project_str)

    ########################################
    # Command - import
    ########################################

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

            if response.upper() == "M":
                self._print("Merging projects...\n")
                projects = import_config(file_path, ImportStrategy.merge)
            elif response.upper() == "R":
                self._print("Replacing projects...\n")
                projects = import_config(file_path, ImportStrategy.overwrite)
            else:
                self._print("Import aborted.\n")
                projects = None

        if not projects:
            return

        self._print("\nThe following projects were imported:")
        for project in projects:
            self._print_project_summary(project)

        self._print("\n")

    ########################################
    # Command - metrics
    ########################################

    def do_metrics(self, line):
        """Print out metrics available for the current project."""
        if not self.current_project:
            self._error("Please select a project first using the 'switch' "
                        "command")
            return

        self._title(self.current_project.name + " Metrics:")
        for metric in sorted(self.current_project.metrics,
                             key=lambda m: m.name):
            self._print(" * {0} ({1})".format(metric.name,
                                              metric.metric_type.display_name()))

            if metric.desc:
                self._print("   - Description: " + metric.desc)

            if metric.value_range:
                self._print("   - Possible Values: "
                            + ", ".join(map(str, metric.value_range)))

            if metric.default_value:
                self._print("   - Default Value: " + str(metric.default_value))

        self._print()

    ########################################
    # Command - tasks
    ########################################

    def do_tasks(self, line):
        """Print out a list of tasks for the current project and accumulated
         metrics for each task.
        """
        parser = ArgumentParser(stdout=self.stdout,
                                prog="tasks",
                                add_help=False)
        parser.add_argument("--details", action="store_true")
        parser.add_argument("pattern", metavar="PATTERN", nargs="?")

        args = parser.parse_args(line.split())
        if not args:
            self._error("Invalid arguments")
            return

        details = args.details
        pattern = args.pattern if args.pattern else "*"

        self._title("Tasks")

        # align printed values for details by finding longest metric name
        metric_names = [m.name for m in self.current_project.metrics]
        metric_names.append("Created"),
        metric_names.append("Last Updated")
        max_name_len = len(max(metric_names, key=len))
        detail_fmt = "    {0:" + str(max_name_len) + "} | {1}"

        for task in sorted(
                filter(lambda t: fnmatch.fnmatch(t.name, pattern),
                       self.current_project.tasks),
                key=lambda t: t.name):
            self._info(" * " + task.name, extra_newline=False)
            if details:
                self._print(" " + "-" * 51)
                for metric in self.current_project.metrics:
                    metric_value = task.value(metric)
                    value = metric.metric_type.to_str(metric_value) \
                        if metric_value else "----"
                    self._print(detail_fmt.format(metric.name, value))
                self._print()
                self._print(detail_fmt.format("Created", task.created))
                self._print(detail_fmt.format("Last Updated",
                                              task.last_updated))
                self._print()

        self._print()

    ########################################
    # Command - task
    ########################################

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
        self._error("Interactive task input is not implemented yet!")
        return False

    def _update_task(self, task_name, args):
        metrics = []
        args_len = len(args)
        for i in range(0, args_len, 2):
            metric_name = args[i]

            # Determine value string
            val_idx = i + 1
            if val_idx >= args_len:
                self._error("Invalid expression. Missing value for: "
                            + metric_name)
                return

            value_str = args[val_idx]

            # Determine metric
            metric = self.current_project.metric(metric_name)
            if not metric:
                self._error("Invalid metric: " + metric_name)
                return

            try:
                value = metric.metric_type.parse(value_str)
            except ParsingError as e:
                self._error(str(e))
                return

            metrics.append((metric, value))

        task = self.current_project.task(task_name)
        for metric, value in metrics:
            try:
                task.record(metric, value)
            except ValueError as e:
                self._error(str(e))
                self.projects.revert()
                return False

        self.projects.save(self.current_project)

        return True

    def _print_task(self, task):
        output = [
            "Created: " + str(task.created),
            "Last Updated: " + str(task.last_updated),
            '\n'
        ]
        for data_point in task.data_points:
            output.append(" {0} -> {1}".format(data_point.metric,
                                               data_point.value))

        self._print("\n".join(output) + "\n")

    ########################################
    # Command - stopwatch
    ########################################

    def do_stopwatch(self, line):
        """Creates a new stopwatch for recording time for a particular task.
        """
        parser = ArgumentParser(stdout=self.stdout,
                                prog="stopwatch",
                                add_help=False)
        parser.add_argument("task", metavar="TASK")
        parser.add_argument("metric", metavar="METRIC", nargs="?")

        args = parser.parse_args(line.split())
        if not args.task:
            self._print()
            self._error("Invalid arguments")
            return

        # Get task with specified name and optional metric
        task = self.current_project.task(args.task, create=False)
        if not task:
            self._error("Task {} does not exist.".format(args.task))
            return

        if args.metric:
            metric = self.current_project.metric(args.metric)
            if not metric:
                self._error("Metric {} does not exist.".format(args.metric))
                return
        else:
            metric = None

        # Create a stop watch and UI
        self._print("\n  (R)eset | (S)tart | (P)ause | S(t)op\n")

        self.stdout.write("  Stopped\t--:--:--\r")
        self.stdout.flush()

        stopwatch_active = True
        stopwatch = StopWatch()
        with cbreak():
            while stopwatch_active:
                user_input_int = ord(self.stdin.read(1))
                if 0 <= user_input_int <= 256:
                    user_input = chr(user_input_int).upper()
                    if user_input == "S":
                        stopwatch.start(tick_callback=self._update_printout)
                    elif user_input == "P":
                        stopwatch.pause()
                    elif user_input == 'R':
                        stopwatch.reset()
                    elif user_input == "T":
                        stopwatch.stop()
                        stopwatch_active = False

        # At this point, stopwatch has been stopped, so now attempt to assign
        # its total duration to the task.
        if metric:
            self._assign_time(task, metric, stopwatch.total)
        else:
            self._assign_time_interactive(task, stopwatch.total)

        self.projects.save(self.current_project)

    def _assign_time(self, task, metric, total):
        task.record(metric, total)
        self._print('  \n\n  Added {} to "{}"\n'.format(total, metric.name))

    def _assign_time_interactive(self, task, total):
        self._title("\n\nAssign Time")
        self._print("The stop watch recorded {}. Assign that time to the "
                    "metrics in this task:\n\n".format(total))

        remainder = total
        duration_metrics = filter(lambda m: m.metric_type is Duration,
                                  self.current_project.metrics)
        for metric in sorted(duration_metrics, key=lambda m: m.name):
            parsed_val = None
            while parsed_val is None:
                value = input("  {} ({} remaining): ".format(metric.name,
                                                             remainder))
                if value.lower() == "rest":
                    parsed_val = remainder
                else:
                    try:
                        parsed_val = Duration.parse(value)
                    except ParsingError as e:
                        self._error(str(e))
                    except:
                        self._error("Invalid duration")

                if parsed_val > remainder:
                    self._error("{} is greater than remaining time from "
                                "stopwatch ({})".format(parsed_val, remainder))
                    parsed_val = None

            task.record(metric, parsed_val)
            remainder -= parsed_val

            if remainder.total_seconds() <= 0:
                break

        self._print()

    def _update_printout(self, total, status):
        """Update printout of current stopwatch value to screen.

        :param total: The total as a :class:`datetime.timedelta`.
        :param status: The current stopwatch status as a string.

        """
        self.stdout.write(" " * 80 + "\r")
        self.stdout.write(colored("  {:7}\t{}\r".format(status, total),
                                  self._stopwatch_status_colors[status]))
        self.stdout.flush()

    def complete_stopwatch(self, text, line, beginx, endidx):
        """Provides support for auto-complete of task name in stopwatch command.
        """
        tasks = Tasks(self.current_project)
        start_index = len("stopwatch ")
        if beginx == start_index:
            return [t.name for t in tasks.starts_with(text)]

        beginning = line[start_index:beginx]
        partial_name = beginning + text
        matches = tasks.starts_with(partial_name)
        return [t.name.replace(beginning, "") for t in matches]

    ########################################
    # Utility methods
    ########################################

    def _title(self, line):
        self._print("\n" + line)
        self._print("-" * min(len(line), 80) + "\n")

    def _success(self, msg, extra_newline=True):
        self._print(msg, 'green', extra_newline)

    def _info(self, msg, extra_newline=True):
        self._print(msg, 'cyan', extra_newline)

    def _warning(self, msg, extra_newline=True, indent=0):
        self._print(" " * indent + "Warning: " + msg, "yellow", extra_newline)

    def _error(self, msg, extra_newline=True, indent=0):
        self._print(" " * indent + "Error: " + msg, "red", extra_newline)

    def _print(self, msg=None, color=None, extra_newline=False):
        if msg and color and self.use_color:
            msg = colored(msg, color)

        if not msg:
            msg = ""

        print(msg, file=self.stdout)
        if extra_newline:
            print(file=self.stdout)