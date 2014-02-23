from maxify.model import *
from maxify.units import (
    Int,
    Duration
)


def configure():
    return [
        Project(name="nep",
                desc="NEP project",
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
        Project(name="test",
                desc="Test Project",
                metrics=[
                    Metric(name="Coding Time",
                           units=Duration)
                ])
    ]