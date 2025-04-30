# tests/test_auth.py
from app.models import User, db
from werkzeug.security import check_password_hash

def test_register_user(client, app):
    # Register a new user.
    response = client.post("/register", data={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    }, follow_redirects=True)
    assert b"Registration successful" in response.data

    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        assert user is not None
        assert user.email == "test@example.com"
        assert check_password_hash(user.password_hash, "password123")

def test_login_logout(client, app):
    # Register user first.
    client.post("/register", data={
        "username": "loginuser",
        "email": "login@example.com",
        "password": "loginpass"
    }, follow_redirects=True)
    
    # Log in the user.
    login_response = client.post("/login", data={
        "username": "loginuser",
        "password": "loginpass"
    }, follow_redirects=True)
    assert b"Dashboard" in login_response.data

    # Log out.
    logout_response = client.get("/logout", follow_redirects=True)
    assert b"Login" in logout_response.data
