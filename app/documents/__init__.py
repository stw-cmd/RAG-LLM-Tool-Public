# app/documents/__init__.py
from flask import Blueprint

# Defines the document blueprint; routes are registered in routes.py
document_bp = Blueprint(
    'document',
    __name__,
    url_prefix='', 
    template_folder='templates'
)