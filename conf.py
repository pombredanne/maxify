from maxify.config import Project
from maxify.units import (
    Int,
    Duration,
    String
)

maxify_proj = Project(name="Maxify",
                      desc="Maxify",
                      nickname="maxify")

nep = Project(name="NEP",
              desc="NEP project",
              nickname="nep")

nep.add_metric(name="Estimated Story Points",
               units=Int,
               value_range=[1, 2, 3, 5, 8, 13],
               default_value=1)
nep.add_metric(name="Final Story Points",
               units=Int,
               value_range=[1, 2, 3, 5, 8, 13],
               default_value=1)
nep.add_metric(name="Research Time",
               units=Duration)
nep.add_metric(name="Coding Time",
               units=Duration)
nep.add_metric(name="Test Time",
               units=Duration)
nep.add_metric(name="Debug Time",
               units=Duration)
nep.add_metric(name="Tool Overhead",
               units=Duration),
nep.add_metric(name="Languages Used",
               units=String)
nep.add_metric(name="Notes",
               units=String)