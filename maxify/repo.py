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

from contextlib import contextmanager

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound

from maxify.data import open_user_data
from maxify.projects import Project
from maxify.log import Logger


class Repository(object):
    """Base class for a data repository that can be used to access program
    data in a way that is agnostic to the underlying data storage mechanism.

    """

    #: Database session used to access data
    db_session = None

    @classmethod
    def init(cls, path, test_mode=False):
        """Initialize the repository with a path to the data store to be
        used.

        :param path: `str` containing the path to the data store.
        :param test_mode: Optional `boolean` indicating whether the repository
            is being used in a test mode (i.e. during unit tests) vs.
            normal operation mode.

        """
        cls.db_session = open_user_data(path, use_static_pool=test_mode)


class Projects(Repository):
    """Repository for accessing projects from the internal data store.

    Projects are identified by the following coordinates: [organization, name],
    in a similar manner to GAV coordinates in Maven, Ivy, etc.  Alternatively,
    for small setups, the organization can be `None`, meaning just a default
    organization store.

    """

    #: String used to separate an organization from a name in a
    #: fully-qualified project name.  For instance, `scopetastic/maxify`
    org_separator = "/"

    log = Logger("projects")

    def __init__(self):
        self.delay_save = False

    def all(self):
        """Get all projects for the data store.

        :return: The set of projects

        """
        return self._unpack(self.db_session.query(Project).all())

    def all_named(self, *names):
        query = self.db_session.query(Project)
        for organization, name in map(Project.split_qualfied_name, names):
            query.filter_by(name=name, organization=organization)

        return self._unpack(query.all())

    def matching_name(self, name):
        """Return list of complete project names that match the partial
        name provided.  The partial name provide will be matched starting
        at the beginning of each qualified name (`org/name`)

        :param name: The partial name to find matches for in the data store.
         The name will be matched starting at the beginning of the
         fully-qualified name of the project.

        :return: `list` of full project names that match the partial name
         argument.

        """
        self.log.debug("Finding full names matching " + name)
        matches = []
        for project in self.db_session.query(Project)\
                .add_columns(Project.name, Project.organization)\
                .all():
            p = Project(name=project.name,
                        organization=project.organization)
            full_name = p.qualified_name
            if full_name.lower().startswith(name):
                matches.append(full_name)

        self.log.debug("Matches: {}", matches)
        return matches

    def get(self, name, organization=None):
        """Get project from the repository with the corresponding name and
        organization.

        :param name: The name of the project.  Valid names include
         fully-qualified names that are prefixed with the organization the
         project belongs to (for instance, `scopetastic/maxify`).  For
         projects not belonging to an organization, an example would be
        `maxify`.
        :param organization: The project's organization.  By default, this is
         `None`, meaning that the project belongs to no organization.

        :return: The project, or `None` if not found.

        """
        if organization is None:
            organization, name = Project.split_qualfied_name(name)

        try:
            project = self.db_session.query(Project) \
                .filter_by(name=name, organization=organization) \
                .one()
            project.unpack()
            return project
        except NoResultFound:
            return None

    @classmethod
    def qualified_name(cls, name, organization):
        if not organization:
            return name
        else:
            return organization + cls.org_separator + name

    @staticmethod
    def _unpack(projects):
        for project in projects:
            project.unpack()
        return projects

    def save(self, project):
        """Save the specified project to the data store.

        :param project: The project to save.

        """
        # Always use lowercase for organization and name for storage
        # purposes
        if project.organization:
            project.organization = project.organization.lower()
        project.name = project.name.lower()
        self.db_session.add(project)
        if not self.delay_save:
            self.db_session.commit()

    def revert(self):
        self.db_session.rollback()

    def delete(self, *projects):
        for project in projects:
            self.db_session.delete(project)

        self.db_session.flush()
        if not self.delay_save:
            self.db_session.commit()

    @contextmanager
    def transaction(self):
        self.delay_save = True
        yield
        self.delay_save = False

        try:
            self.db_session.commit()
        except SQLAlchemyError:
            self.db_session.rollback()
            raise