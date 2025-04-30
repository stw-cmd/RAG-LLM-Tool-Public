# app/queries/__init__.py
from flask import Blueprint

# Defines the query blueprint; routes are registered in routes.py
query_bp = Blueprint('query', __name__)