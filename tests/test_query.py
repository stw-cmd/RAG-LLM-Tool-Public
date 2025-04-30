# tests/test_query.py
import pytest
from app.models import QueryHistory, db

# Helper functions for authentication.
def register(client, username, email, password):
    return client.post("/register", data={
        "username": username,
        "email": email,
        "password": password
    }, follow_redirects=True)

def login(client, username, password):
    response = client.post("/login", data={
        "username": username,
        "password": password
    }, follow_redirects=True)
    assert b"Dashboard" in response.data
    return response

# Monkey-patch RetrievalQA so that no external API calls are made.
@pytest.fixture(autouse=True)
def patch_qa(monkeypatch):
    from langchain.chains import RetrievalQA
    class FakeQAChain:
        def run(self, question):
            return "Fake answer."
    monkeypatch.setattr(RetrievalQA, "from_chain_type", lambda **kwargs: FakeQAChain())

def test_process_query(client, app):
    with client:
        register(client, "queryuser", "query@example.com", "querypass")
        login(client, "queryuser", "querypass")
    
        response = client.post("/query", data={
            "question": "Test question",
            "csrf_token": "dummy"  # CSRF is disabled in tests.
        }, follow_redirects=True)
        # Verify that we remain on the dashboard.
        assert b"Dashboard" in response.data
    
    with app.app_context():
        query_obj = QueryHistory.query.filter_by(question="Test question").first()
        assert query_obj is not None
        assert query_obj.answer == "Fake answer."
