# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

# Database instance
db = SQLAlchemy()

# Mail instance
mail = Mail()