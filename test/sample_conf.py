from maxify.projects import Project
from maxify.metrics import Metric, Number, Duration


def configure():
    project1 = Project(name="nep", desc="NEP project")
    project1.add_metric(Metric(name="Story Points",
                               project=project1,
                               metric_type=Number,
                               value_range=[1, 2, 3, 5, 8, 13],
                               default_value=1))
    project1.add_metric(Metric(name="Final Story Points",
                               project=project1,
                               metric_type=Number,
                               value_range=[1, 2, 3, 5, 8, 13],
                               default_value=1))
    project1.add_metric(Metric(name="Research Time",
                               project=project1,
                               metric_type=Duration))
    project1.add_metric(Metric(name="Coding Time",
                               project=project1,
                               metric_type=Duration))
    project1.add_metric(Metric(name="Test Time",
                               project=project1,
                               metric_type=Duration))
    project1.add_metric(Metric(name="Debug Time",
                               project=project1,
                               metric_type=Duration))
    project1.add_metric(Metric(name="Tool Overhead",
                               project=project1,
                               metric_type=Duration))

    project2 = Project(name="test", desc="Test Project")
    project2.add_metric(Metric(name="Coding Time",
                               project=project2,
                               metric_type=Duration))

    return [project1, project2]