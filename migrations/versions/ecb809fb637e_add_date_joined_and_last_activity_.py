"""Add date_joined and last_activity columns to User model

Revision ID: ecb809fb637e
Revises: 05f5755ff93f
Create Date: 2025-04-11 12:16:47.670061

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ecb809fb637e'
down_revision = '05f5755ff93f'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns with server defaults so that existing rows get valid values.
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.text("0")))
        batch_op.add_column(sa.Column('date_joined', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()))
        batch_op.add_column(sa.Column('last_activity', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()))
    # Remove the server defaults, so future inserts rely on application defaults.
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('is_admin', server_default=None)
        batch_op.alter_column('date_joined', server_default=None)
        batch_op.alter_column('last_activity', server_default=None)

def downgrade():
    # To reverse the changes:
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('last_activity')
        batch_op.drop_column('date_joined')
        batch_op.drop_column('is_admin')