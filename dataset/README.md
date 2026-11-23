# Synthetic Dataset

This folder contains generators, CSV exports, RAG policy documents, and the database seeding script for the **Enterprise AI Operations Assistant**.

## Contents

| Path | Purpose |
|---|---|
| `generators/` | Deterministic Faker-based synthetic data builders |
| `csv/` | One CSV file per database table |
| `documents/` | Company policy documents for a future RAG pipeline |
| `seed_database.py` | Create tables and insert generated records into PostgreSQL |

## Target volumes

| Table | Count |
|---|---|
| roles | 3 |
| users | 20 |
| customers | 500 |
| products | 100 |
| orders | 2,000 |
| order_items | 4,000–6,000 |
| payments | 1,800–2,000 |
| support_tickets | 500 |

## Consistency rules

- Orders always reference existing customers.
- Order items always reference existing orders and products.
- Order `subtotal` equals the sum of item `line_total` values.
- Order `total_amount` equals `subtotal + tax_amount + shipping_amount`.
- Payments reference existing orders.
- Support tickets reference valid customers; order and assignee links are optional but validated when present.
- Emails, SKUs, order numbers, payment references, and ticket numbers are unique.
- Generation uses a fixed seed (`DATASET_SEED`, default `42`) for reproducibility.

## Generate CSVs only

From the project root:

```bash
PYTHONPATH=. python -m dataset.generators.export_csv
```

## Seed PostgreSQL

1. Copy `.env.example` to `.env` and set `DATABASE_URL`.
2. Create the database: `createdb enterprise_ai`
3. Run:

```bash
PYTHONPATH=backend:. python dataset/seed_database.py
```

The seeder is safely re-runnable: unique-key conflicts are skipped.

## Policy documents

Markdown files in `documents/` are intended for later RAG ingestion. Do not delete them when regenerating CSVs.
