"""Module defining utility functions for Maxify.

"""

from collections import namedtuple
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


class _Enum(object):
    """Rudimentatry implementation of functional API for enums in Python 3.4.
    This is a polyfil for Python 3.0 - 3.3.

    """
    def __call__(self, name, members):
        tuple_type = namedtuple(name + "Type", field_names=members)

        member_values = {members[i]: i + 1 for i in range(0, len(members))}
        return tuple_type(**member_values)

Enum = _Enum()