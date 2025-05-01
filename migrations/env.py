import logging
from logging.config import fileConfig

from flask import current_app
from alembic import context

# Alembic Config object, provides access to ini options
config = context.config

# Set up Python logging per the Alembic config file
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# Override the sqlalchemy.url from alembic.ini with the Flask app’s setting
config.set_main_option(
    'sqlalchemy.url',
    current_app.config['SQLALCHEMY_DATABASE_URI']
)

# Import your SQLAlchemy db and all models so that
# db.metadata contains Table information for autogeneration
from app.extensions import db
import app.models  # registers User, UploadedDocument, Folder, QueryHistory, etc.

# This is what Alembic uses to compare current DB vs. models
target_metadata = db.metadata


def get_engine():
    """
    Return the SQLAlchemy Engine from Flask-Migrate’s extension.
    """
    return current_app.extensions['migrate'].db.engine


def run_migrations_offline():
    """
    Run migrations in 'offline' mode.
    This emits SQL to the script output, without needing a live DB connection.
    """
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """
    Run migrations in 'online' mode.
    This creates a connection to the DB and applies migrations directly.
    """
    def process_revision_directives(context, revision, directives):
        # Prevent generation of an empty migration
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    connectable = get_engine()
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives,
            **current_app.extensions['migrate'].configure_args
        )

        with context.begin_transaction():
            context.run_migrations()


# Choose offline or online based on context
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
