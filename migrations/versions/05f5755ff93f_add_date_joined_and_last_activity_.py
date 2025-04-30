"""Add date_joined and last_activity columns to User model

Revision ID: 05f5755ff93f
Revises: 7e1f1cdbcca1
Create Date: 2025-04-11 12:05:28.175902

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '05f5755ff93f'
down_revision = '7e1f1cdbcca1'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Add the columns as nullable
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('date_joined', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('last_activity', sa.DateTime(), nullable=True))

    # Step 2: Update existing rows with a default value. Using SQLite’s CURRENT_TIMESTAMP.
    op.execute("UPDATE user SET date_joined = CURRENT_TIMESTAMP WHERE date_joined IS NULL")
    op.execute("UPDATE user SET last_activity = CURRENT_TIMESTAMP WHERE last_activity IS NULL")

    # Step 3: Alter the columns to be non-nullable.
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('date_joined', nullable=False)
        batch_op.alter_column('last_activity', nullable=False)

def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('last_activity')
        batch_op.drop_column('date_joined')