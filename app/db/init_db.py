from app.db.session import Base, engine

# Import models so SQLAlchemy knows about them.
from app.models import Customer  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)