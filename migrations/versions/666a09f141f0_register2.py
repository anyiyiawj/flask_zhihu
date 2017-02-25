"""register2

Revision ID: 666a09f141f0
Revises: 2236f5ae1aac
Create Date: 2017-02-25 16:51:13.462765

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '666a09f141f0'
down_revision = '2236f5ae1aac'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('confirmed', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'confirmed')
    # ### end Alembic commands ###
