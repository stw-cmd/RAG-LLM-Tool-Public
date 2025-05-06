# tests/test_performance.py

import pytest
from app import create_app
from app.extensions import db

# Create a test client for the Flask app
@pytest.fixture
def client(tmp_path, monkeypatch):
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()

# Measure the median time to GET /dashboard
@pytest.mark.benchmark(group="dashboard")
def test_dashboard_performance(benchmark, client):
    # Register and login a user
    client.post("/register", data={"email":"a@b.com","password":"p","confirm":"p"})
    client.post("/login",    data={"email":"a@b.com","password":"p"})
    def call_dashboard():
              # Follow the redirect into the dashboard page after login
        resp = client.get("/dashboard", follow_redirects=True)
        assert resp.status_code == 200
    # Run the benchmark
    benchmark(call_dashboard)

# Measure the median time to perform CRUD operations on folders
@pytest.mark.benchmark(group="folder_crud")
def test_folder_crud_performance(benchmark, client):
    # Register and login a user
    client.post("/register", data={"email":"x@x.com","password":"p","confirm":"p"})
    client.post("/login",    data={"email":"x@x.com","password":"p"})
    def folder_flow():
        r1 = client.post("/create_folder", data={"folder_name":"foo"})
        assert r1.status_code == 302
        r2 = client.post("/rename_folder/1", data={"new_name":"bar"})
        assert r2.status_code == 302
        r3 = client.post("/delete_folder/1")
        assert r3.status_code == 302
    # Run the benchmark
    benchmark(folder_flow)
