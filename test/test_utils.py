"""
Unit tests for the ``maxify.utils`` module.
"""

from maxify.utils import *


def test_sorted_naturally():
    values = ["A 1", "A 10", "A 2", "b"]
    assert sorted_naturally(values) == ["A 1", "A 2", "A 10", "b"]

    values = [("b", None), ("A 1", 1), ("A 10", 10), ("A 2", 2)]
    assert sorted_naturally(values, key=lambda v: v[0]) == [
        ("A 1", 1),
        ("A 2", 2),
        ("A 10", 10),
        ("b", None)
    ]


def test_enum():
    colors = Enum("Colors", ["red", "green", "blue"])

    assert hasattr(colors, "red")
    assert hasattr(colors, "blue")
    assert hasattr(colors, "green")