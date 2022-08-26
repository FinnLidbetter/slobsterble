"""
Add the delete_requested column to the User table and fix a UserVerification migration error.

Revision ID: 377d7daad8e1
Revises: 6b36da38e71f
Create Date: 2022-08-25 19:28:49.502096

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '377d7daad8e1'
down_revision = '6b36da38e71f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('delete_requested', sa.Boolean(), nullable=True))
    op.execute('UPDATE user SET delete_requested=false')
    with op.batch_alter_table('user') as batch_op:
        batch_op.alter_column('delete_requested', nullable=False)
    with op.batch_alter_table('user_verification') as batch_op:
        batch_op.alter_column(
            'token_hash',
            existing_type=sa.VARCHAR(length=256),
            type_=sa.String(length=255),
            existing_nullable=False)
        batch_op.alter_column(
            'username',
            existing_type=sa.VARCHAR(length=256),
            type_=sa.String(length=255, collation='NOCASE'),
            existing_nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_verification') as batch_op:
        batch_op.alter_column(
            'username',
            existing_type=sa.String(length=255, collation='NOCASE'),
            type_=sa.VARCHAR(length=256),
            existing_nullable=False)
        batch_op.alter_column(
            'token_hash',
            existing_type=sa.String(length=255),
            type_=sa.VARCHAR(length=256),
            existing_nullable=False)
    op.drop_column('user', 'delete_requested')
    # ### end Alembic commands ###
