from maxify.model import *
from maxify.units import (
    Int,
    Duration
)


def configure():
    return [
        Project(name="maxify",
                desc="Maxify client",
                metrics=[
                    Metric(
                        name="Story Points",
                        desc="Estimated story points for task",
                        units=Int,
                        value_range=[1, 2, 3, 5, 8, 13],
                        default_value=3
                    ),
                    Metric(name="Final Story Points",
                           desc="Actual story points for task",
                           units=Int,
                           value_range=[1, 2, 3, 5, 8, 13],
                           default_value=3),
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
                ])
    ]