from maxify.model import *
from maxify.units import (
    Int,
    Duration
)


def configure():
    return [
        Project(name="NEP",
                desc="NEP project",
                nickname="nep",
                metrics=[
                    Metric(name="Story Points",
                           units=Int,
                           value_range=[1, 2, 3, 5, 8, 13],
                           default_value=1),
                    Metric(name="Final Story Points",
                           units=Int,
                           value_range=[1, 2, 3, 5, 8, 13],
                           default_value=1),
                    Metric(name="Research Time",
                           units=Duration),
                    Metric(name="Coding Time",
                           units=Duration),
                    Metric(name="Test Time",
                           units=Duration),
                    Metric(name="Debug Time",
                           units=Duration),
                    Metric(name="Tool Overhead",
                           units=Duration)
                ]),
        Project(name="Test Project",
                desc="Test Project",
                nickname="test",
                metrics=[
                    Metric(name="Coding Time",
                           units=Duration)
                ])
    ]