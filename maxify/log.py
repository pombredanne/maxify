import logbook


maxify_log_group = logbook.LoggerGroup(level=logbook.DEBUG)
maxify_log_group.disabled = True


def enable_loggers():
    maxify_log_group.disabled = False


class Logger(logbook.Logger):
    def __init__(self, name, level=0):
        super(Logger, self).__init__(name, level)
        maxify_log_group.add_logger(self)