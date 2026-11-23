"""Database statistics service."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Customer,
    Order,
    OrderItem,
    Payment,
    Product,
    Role,
    SupportTicket,
    User,
)
from app.schemas.stats import DatabaseStatsResponse


def get_database_stats(db: Session) -> DatabaseStatsResponse:
    """Return row counts for every business table."""

    def count(model) -> int:
        return int(db.scalar(select(func.count()).select_from(model)) or 0)

    counts = {
        "roles": count(Role),
        "users": count(User),
        "customers": count(Customer),
        "products": count(Product),
        "orders": count(Order),
        "order_items": count(OrderItem),
        "payments": count(Payment),
        "support_tickets": count(SupportTicket),
    }
    return DatabaseStatsResponse(
        **counts,
        total_records=sum(counts.values()),
    )
