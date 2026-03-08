"""Add department_id to users table

Revision ID: add_department_id_to_users
Revises: 26c21437e39f
Create Date: 2026-03-04 01:16:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_department_id_to_users'
down_revision = '26c21437e39f'
branch_labels = None
depends_on = None


def upgrade():
    # Add department_id foreign key to users
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('department_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_users_department_id', 'users', ['department_id'], ['departments.id'])
        batch_op.create_index('ix_users_department_id', ['department_id'], unique=False)


def downgrade():
    # Remove department_id foreign key from users
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_users_department_id', table_name='users')
        batch_op.drop_constraint('fk_users_department_id', type_='foreignkey')
        batch_op.drop_column('department_id')
