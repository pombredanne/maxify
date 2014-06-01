"""Module defining utility functions for Maxify.

"""

import argparse
from functools import partial
import re

_number_re = re.compile("([0-9]+)")


def sorted_naturally(l, key=None, reverse=False):
    """Returns the provided list of values sorted in natural order.

    Example:

        >>> values = ["A 1", "A 10", "A 2", "b"]
        >>> print(sorted_naturally(values))
        ... ["A 1", "A 2", "A 10", "b"]

    :param list l: List of objects to sort.
    :param function key: Optional function to return key by which to sort values
    in ``l``.  If not specified, values will be used directly (they must be
    strings if no key function is specified).
    :param bool reverse: True to sort values in reverse order.

    :return: The list of values sorted in natural order.
    :rtype: list

    """
    if key:
        key_func = partial(_alphanum_key, prop_getter=key)
    else:
        key_func = _alphanum_key

    return sorted(l, key=key_func, reverse=reverse)


def _convert_if_numeric(s):
    return int(s) if s.isdigit() else s.lower()


def _alphanum_key(s, prop_getter=None):
    if prop_getter is not None:
        s = prop_getter(s)
    return [_convert_if_numeric(c) for c in _number_re.split(s)]


class ArgumentParser(argparse.ArgumentParser):
    """Extension of the built-in ``ArgumentParser`` that allows errors to not
    result in program termination.

    :param stdout: File-like object to use for printing output to.
    :param kwargs: Normal keyword arguments accepted by the
        :class:`argparse.ArgumentParser` init method.

    """
    def __init__(self, stdout, **kwargs):
        super().__init__(**kwargs)
        self.stdout = stdout

    def parse_args(self, args=None, namespace=None):
        try:
            args, argv = self.parse_known_args(args, namespace=namespace)
        except:
            return None

        if argv:
            self.error("unrecognized arguments: " + " ".join(argv))
            return None

        return args

    def error(self, message):
        self.print_usage(file=self.stdout)