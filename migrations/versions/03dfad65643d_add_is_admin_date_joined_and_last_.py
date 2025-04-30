"""Add is_admin, date_joined, and last_activity columns to User model with defaults

Revision ID: 03dfad65643d
Revises: 055132aaa4c0
Create Date: 2025-04-11 13:14:57.299884

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '03dfad65643d'
down_revision = '055132aaa4c0'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the temporary table if it exists. This prevents the IntegrityError.
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_user")

    # Add new columns with server-side defaults so existing rows get valid values.
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'is_admin', sa.Boolean(),
            nullable=False,
            server_default=sa.text("0")  # This sets the default to 0 (False)
        ))
        batch_op.add_column(sa.Column(
            'date_joined', sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp()  # Use the database current timestamp
        ))
        batch_op.add_column(sa.Column(
            'last_activity', sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp()
        ))

    # Optionally, remove the server defaults (if you want inserts to specify values)
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('is_admin', server_default=None)
        batch_op.alter_column('date_joined', server_default=None)
        batch_op.alter_column('last_activity', server_default=None)

def downgrade():
    # In the downgrade, drop the columns
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('last_activity')
        batch_op.drop_column('date_joined')
        batch_op.drop_column('is_admin')