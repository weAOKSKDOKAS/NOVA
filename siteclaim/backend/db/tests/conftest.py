"""Hermetic DB fixtures — every test builds its own offline seed in a temp dir.

No network, no model load: the seed bakes deterministic vectors. Tests never touch
the committed ``sitesource.db``.
"""

import pytest

from db import seed, store


@pytest.fixture(scope="session")
def db_path(tmp_path_factory):
    path = tmp_path_factory.mktemp("sitesource") / "test.db"
    seed.build_database(path)
    return path


@pytest.fixture
def conn(db_path):
    connection = store.get_connection(db_path)
    yield connection
    connection.close()


# A scope query rich in the electrical closeout vocabulary, used by the hero tests.
ELECTRICAL_SCOPE_QUERY = (
    "LV main switchboard sub-mains final circuits lighting installation cable "
    "containment busbar trunking power distribution testing and commissioning"
)
