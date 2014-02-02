import pytest

from maxify.model import open_user_data

@pytest.fixture
def db_session():
    return open_user_data(":memory:", True)