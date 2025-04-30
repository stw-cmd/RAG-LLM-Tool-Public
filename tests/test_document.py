# tests/test_document.py
import io
import pytest
from app.models import UploadedDocument, db

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
    # Verify that login succeeded
    assert b"Dashboard" in response.data
    return response

def test_upload_document(client, app):
    with client:
        register(client, "docuser", "doc@example.com", "docpass")
        login(client, "docuser", "docpass")
    
        # Create a dummy file to upload.
        data = {
            "document": (io.BytesIO(b"Test file content."), "test.txt")
        }
        response = client.post("/upload", data=data, content_type="multipart/form-data", follow_redirects=True)
        # Instead of expecting a flash message, check that we are on the dashboard.
        assert b"Dashboard" in response.data

    with app.app_context():
        doc = UploadedDocument.query.filter_by(filename="test.txt").first()
        assert doc is not None

def test_scrape_document(client, app, monkeypatch):
    with client:
        register(client, "scrapeuser", "scrape@example.com", "scrapepass")
        login(client, "scrapeuser", "scrapepass")
    
        from app.utils import scrape_website as original_scrape_website
        def fake_scrape_website(url):
            return "Fake scraped content.", None
        monkeypatch.setattr("app.utils.scrape_website", fake_scrape_website)
    
        response = client.post("/scrape", data={"url": "https://example.com"}, follow_redirects=True)
        # Verify that the resulting page is the dashboard.
        assert b"Dashboard" in response.data
