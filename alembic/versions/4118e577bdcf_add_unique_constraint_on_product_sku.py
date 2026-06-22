"""add unique constraint on product sku

Revision ID: 4118e577bdcf
Revises: faa0d6559131
Create Date: 2026-06-22 13:34:44.866688

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4118e577bdcf'
down_revision: Union[str, Sequence[str], None] = 'faa0d6559131'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_products_sku', ['sku'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_constraint('uq_products_sku', type_='unique')
