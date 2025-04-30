# app/models.py
import datetime
from flask_login import UserMixin
from app.extensions import db

# User model
class User(UserMixin, db.Model):
    # Atttributes/columns of the User table
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # Boolean value to indicate if the user is an admin - False by default
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Timestamps
    date_joined = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        nullable=False
    )
    last_activity = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        nullable=False
    )

    # Relationships to other models
    documents = db.relationship(
        "UploadedDocument", backref="user", lazy=True
    )
    queries = db.relationship(
        "QueryHistory", backref="user", lazy=True
    )
    folders = db.relationship(
        "Folder", backref="user", lazy=True
    )

# Folder model for organising user-uploaded documents
class Folder(db.Model):
    # Attributes/columns of the Folder table
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

# Uploaded documents model for storing metadata about user-uploaded documents
class UploadedDocument(db.Model):
    # Attributes/columns of the uploaded document table
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(50))
    upload_date = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )
    folder_id = db.Column(
        db.Integer,
        db.ForeignKey('folder.id'),
        nullable=True
    )
    folder = db.relationship('Folder', backref='documents', lazy=True)

# Query history model for storing user queries, responses, and timestamps
class QueryHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    timestamp = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )