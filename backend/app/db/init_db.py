"""Create database tables from SQLAlchemy models."""

from app.db.base import Base
from app.db.session import engine

# Import models so they register with Base.metadata
from app.models import (  # noqa: F401
    Conversation,
    Customer,
    DocumentEmbedding,
    Message,
    Order,
    OrderItem,
    Payment,
    Product,
    Role,
    SupportTicket,
    User,
)


def init_db() -> None:
    """Create all tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database tables created successfully.")
