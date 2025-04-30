# app/auth/routes.py
import logging
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db, mail
from app.models import User
from . import auth_bp
from .forms import RegistrationForm, LoginForm

logger = logging.getLogger(__name__)

# Token utility functions for password reset
def generate_reset_token(app, email):
    # Create a URL-safe token for the given email
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return s.dumps(email, salt="password-reset-salt")


def confirm_reset_token(app, token, expiration=3600):
    # Confirm the token is valid and not expired
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt="password-reset-salt", max_age=expiration)
    except (SignatureExpired, BadSignature) as e:
        # Log the error and return None if the token is invalid or expired
        logger.error("Token error: %s", e)
        return None
    return email

# User Registration
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    # On POST, validate form data
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip()
        password = form.password.data.strip()
        # Check for existing username or email
        if User.query.filter_by(username=username).first():
            flash("Username already exists.")
            return redirect(url_for("auth.register"))
        if User.query.filter_by(email=email).first():
            flash("Email already registered.")
            return redirect(url_for("auth.register"))
        # Create new user with a hashed password
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        try:
            db.session.add(user)
            db.session.commit()
            flash("Registration successful. Please log in.")
            return redirect(url_for("auth.login"))
        except Exception as e:
            # Roll back session in case of error and flash error message
            db.session.rollback()
            logger.error("Error during registration: %s", e)
            flash("An error occurred during registration.")
    # Render the registration form
    return render_template("register.html", form=form)

# User Login
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    # On POST, validate form data
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data.strip()
        # Look up user by username
        user = User.query.filter_by(username=username).first()

        # Check password hash
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid username or password.")
            return redirect(url_for("auth.login"))
        # Log in the user
        login_user(user)
        # Set next page to redirect to
        next_page = request.args.get("next")
        if not next_page or not next_page.startswith("/"):
            next_page = url_for("dashboard")
        return redirect(next_page)
    # Render the login form
    return render_template("login.html", form=form)

# User Logout
@auth_bp.route("/logout")
@login_required
def logout():
    # Log out the user and redirect to login page
    logout_user()
    return redirect(url_for("auth.login"))

# Forgot Password
@auth_bp.route("/forgot", methods=["GET", "POST"])
def forgot_password():
    # Handle form submission for password reset
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        # Validate email input
        if not email:
            flash("Email is required.")
            return redirect(url_for("auth.forgot_password"))

        # Look up user by email
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("No account associated with that email.")
            return redirect(url_for("auth.forgot_password"))

        # Generate a password reset token and URL
        token = generate_reset_token(current_app, email)
        reset_url = url_for("auth.reset_password", token=token, _external=True)

        # Deliver resset link to user
        # TODO: send `reset_url` via email using `mail.send_message(...)`
        # For demo purposes, we log the URL instead of sending an email
        logger.info("Password reset link (demo): %s", reset_url)
        flash("A password reset link has been sent to your email (check console in demo).")
        return redirect(url_for("auth.login"))

    return render_template("forgot_password.html")

# Reset Password
@auth_bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    # Verify the token and extract the email
    email = confirm_reset_token(current_app, token)
    if not email:
        flash("The reset link is invalid or has expired.")
        return redirect(url_for("auth.forgot_password"))

    # Handle form submission for password reset
    if request.method == "POST":
        new_password = request.form.get("password", "").strip()
        # Validate new password input
        if not new_password:
            flash("Password is required.")
            return redirect(url_for("auth.reset_password", token=token))

        # Look up user by email
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("User not found.")
            return redirect(url_for("auth.forgot_password"))

        try:
            # Update the user's password
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash("Your password has been reset. Please log in.")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            logger.error("Error resetting password: %s", e)
            flash("An error occurred. Please try again.")
    # Render the reset password form
    return render_template("reset_password.html")