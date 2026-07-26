from sqlalchemy.orm import DeclarativeBase


# Every model class we write will inherit from this Base. SQLAlchemy uses it
# as a registry: Base.metadata ends up holding the definition of every table,
# which is exactly what Alembic reads to figure out what migrations to create.
class Base(DeclarativeBase):
    pass