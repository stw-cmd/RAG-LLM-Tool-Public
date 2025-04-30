# app/auth/__init__.py
from flask import Blueprint

# Defines the auth blueprint; routes are registered in routes.py
auth_bp = Blueprint('auth', __name__)