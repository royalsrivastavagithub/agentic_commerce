# Import all the models, so that Base has them before being
# imported by Alembic or database initialization scripts.
from app.db.session import Base
from app.models.user import User
from app.models.product import Product
from app.models.category import Category
from app.models.address import Address
