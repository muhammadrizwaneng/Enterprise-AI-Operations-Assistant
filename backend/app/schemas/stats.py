"""Pydantic schemas for API responses."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    app_name: str
    environment: str


class DatabaseStatsResponse(BaseModel):
    roles: int = Field(..., ge=0)
    users: int = Field(..., ge=0)
    customers: int = Field(..., ge=0)
    products: int = Field(..., ge=0)
    orders: int = Field(..., ge=0)
    order_items: int = Field(..., ge=0)
    payments: int = Field(..., ge=0)
    support_tickets: int = Field(..., ge=0)
    total_records: int = Field(..., ge=0)
