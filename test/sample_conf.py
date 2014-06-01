from maxify.projects import Project, Number, Duration

project1 = Project(name="nep", desc="NEP project")
project1.add_metric(name="Story Points",
                    metric_type=Number,
                    value_range=[1, 2, 3, 5, 8, 13],
                    default_value=1)
project1.add_metric(name="Final Story Points",
                    metric_type=Number,
                    value_range=[1, 2, 3, 5, 8, 13],
                    default_value=1)
project1.add_metric(name="Research Time",
                    metric_type=Duration)
project1.add_metric(name="Coding Time",
                    metric_type=Duration)
project1.add_metric(name="Test Time",
                    metric_type=Duration)
project1.add_metric(name="Debug Time",
                    metric_type=Duration)
project1.add_metric(name="Tool Overhead",
                    metric_type=Duration)

project2 = Project(name="test", desc="Test Project")
project2.add_metric(name="Coding Time",
                    metric_type=Duration)

projects = [
    project1,
    project2
]