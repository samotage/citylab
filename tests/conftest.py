"""Test fixtures for CityLab."""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _force_test_database():
    """Force all tests to use the test database.

    This is a session-scoped autouse fixture that sets DATABASE_URL
    before any test runs. NEVER remove, bypass, or weaken this fixture.
    """
    os.environ["DATABASE_URL"] = "postgresql://samotage@localhost:5432/citylab_test"
    yield
    # Don't clean up — let the process end naturally


@pytest.fixture(scope="session")
def app(_force_test_database):
    """Create application for testing."""
    from citylab import create_app

    app = create_app(testing=True)

    # Create tables in test database
    from citylab.extensions import db

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Database session that rolls back after each test."""
    from citylab.extensions import db

    with app.app_context():
        # Begin a nested transaction
        db.session.begin_nested()
        yield db.session
        db.session.rollback()
