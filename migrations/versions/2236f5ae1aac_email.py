"""email

Revision ID: 2236f5ae1aac
Revises: 588bd570b7bf
Create Date: 2017-02-25 12:15:08.864770

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2236f5ae1aac'
down_revision = '588bd570b7bf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('email', sa.String(length=64), nullable=True))
    op.add_column('users', sa.Column('password_hash', sa.String(length=128), nullable=True))
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'email')
    # ### end Alembic commands ###
