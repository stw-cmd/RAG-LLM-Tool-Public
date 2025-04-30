# tests/conftest.py
import os
import sys
import pytest

# Ensure the project root is added so our local app.py is imported.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.__init__ import create_app
from app.extensions import db

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    # Disable CSRF in tests so tokens aren’t required
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # in-memory database
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
