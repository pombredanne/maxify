"""Utility module for performing some basic setup around runtime logging.
"""

import logbook

# Create a log group specific to the application, and control its logging
# level individually.
maxify_log_group = logbook.LoggerGroup(level=logbook.DEBUG)
maxify_log_group.disabled = True


def enable_loggers():
    """Enable debug logging for application components."""
    maxify_log_group.disabled = False


class Logger(logbook.Logger):
    """Extension of the basic :class:`logbook.Logger` class that automatically
    adds the logger to the program's logging group.

    :param name: The name of the logger.
    :param level: The log level for the logger.

    """
    def __init__(self, name, level=0):
        super(Logger, self).__init__(name, level)
        maxify_log_group.add_logger(self)