"""Module containing classes/methods for implementing a data repository to
provide other parts of the application with access to the underlying data
model without exposing those components to its inner workings.

Example: Getting a project

>>> project.
>>> project = Projects().project("test", "org.scopetastic")
>>> for metric in project.metrics:
...    # Do something here
...    pass
>>> tasks = project.tasks

"""

from sqlalchemy.orm.exc import NoResultFound
from maxify.model import *


class Repository(object):
    db_session = None

    @classmethod
    def init(cls, path):
        cls.db_session = open_user_data(path)


class Projects(Repository):
    """Repository for accessing projects from the internal data store.

    Projects are identified by the following coordinates: [organization, name],
    in a similar manner to GAV coordinates in Maven, Ivy, etc.  Alternatively,
    for small setups, the organization can be `None`, meaning just a default
    organization store.

    """

    def all(self):
        """Get all projects for the data store.

        :return: The set of projects

        """
        return self._unpack(self.db_session.query(Project).all())

    def get(self, name, organization=None):
        """Get project from the repository with the corresponding name and
        organization.

        :param name: The name of the project
        :param organization: The project's organization.  By default, this is
         `None`, meaning that the project belongs to no organization.

        :return: The project, or `None` if not found.

        """
        try:
            project = self.db_session.query(Project) \
                .filter_by(name=name, organization=organization) \
                .one()
            project.unpack()
            return project
        except NoResultFound:
            return None

    @staticmethod
    def _unpack(projects):
        for project in projects:
            project.unpack()
        return projects

    def save(self, project):
        """Save the specified project to the data store.

        :param project: The project to save.

        """
        self.db_session.add(project)
        self.db_session.commit()