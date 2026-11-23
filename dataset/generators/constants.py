"""Dataset generation constants and target volumes."""

from pathlib import Path

# Deterministic seed for reproducible synthetic data
DEFAULT_SEED = 42

# Target record counts
ROLE_COUNT = 3
USER_COUNT = 20
CUSTOMER_COUNT = 500
PRODUCT_COUNT = 100
ORDER_COUNT = 2000
ORDER_ITEM_MIN = 4000
ORDER_ITEM_MAX = 6000
PAYMENT_MIN = 1800
PAYMENT_MAX = 2000
SUPPORT_TICKET_COUNT = 500

# Business vocabularies
ROLE_DEFINITIONS = [
    ("admin", "Full system access and configuration privileges."),
    ("support_agent", "Handles customer support tickets and escalations."),
    ("operations_manager", "Oversees orders, fulfillment, and operational KPIs."),
]

DEPARTMENTS = [
    "Customer Support",
    "Operations",
    "Sales",
    "Finance",
    "Product",
    "IT",
]

PRODUCT_CATEGORIES = [
    "Laptops",
    "Monitors",
    "Peripherals",
    "Networking",
    "Storage",
    "Software Licenses",
    "Office Furniture",
    "Accessories",
]

ORDER_STATUSES = [
    "pending",
    "confirmed",
    "processing",
    "shipped",
    "delivered",
    "cancelled",
    "returned",
    "overdue",
]

# Approximate distribution weights for order statuses
ORDER_STATUS_WEIGHTS = [8, 12, 15, 18, 30, 7, 5, 5]

PAYMENT_METHODS = [
    "credit_card",
    "debit_card",
    "bank_transfer",
    "paypal",
    "invoice",
]

PAYMENT_STATUSES = [
    "pending",
    "completed",
    "failed",
    "refunded",
    "partially_refunded",
]

TICKET_STATUSES = [
    "open",
    "in_progress",
    "waiting_customer",
    "resolved",
    "closed",
]

TICKET_PRIORITIES = ["low", "medium", "high", "urgent"]
TICKET_PRIORITY_WEIGHTS = [25, 45, 22, 8]

TICKET_CATEGORIES = [
    "billing",
    "shipping",
    "product_defect",
    "refund_request",
    "account",
    "general_inquiry",
]

TAX_RATE = 0.08
SHIPPING_FLAT = 9.99
SHIPPING_FREE_THRESHOLD = 150.00

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_DIR = PROJECT_ROOT / "dataset" / "csv"
DOCUMENTS_DIR = PROJECT_ROOT / "dataset" / "documents"
