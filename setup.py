import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ["test"]
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren"t loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name="Maxify",
    version="0.1",
    description="Maxify is a utility for keeping detailed track of "
                "development time for project tasks in a fast and easy "
                "manner.",
    author="Ross Bayer",
    author_email="rossbayer@sicessolutions.com",
    url="http://www.sicessolutions.com",
    install_requires=[
        "pyyaml",
        "numpy",
        "sqlalchemy",
        "colorama",
        "termcolor",
        "logbook"
    ],
    tests_requires=[
        "pytest",
        "pytest-cov"
    ],
    cmdclass={
        "test": PyTest
    }
)
