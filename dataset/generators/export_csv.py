"""Export generated dataset tables to CSV files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from dataset.generators.constants import CSV_DIR, DEFAULT_SEED
from dataset.generators.generate import generate_dataset, summarize_dataset


TABLE_ORDER = [
    "roles",
    "users",
    "customers",
    "products",
    "orders",
    "order_items",
    "payments",
    "support_tickets",
]


def export_dataset_to_csv(
    dataset: dict[str, list[dict[str, Any]]] | None = None,
    output_dir: Path | None = None,
    seed: int = DEFAULT_SEED,
) -> dict[str, Path]:
    """
    Write one CSV file per table into dataset/csv/.

    Returns a mapping of table name -> written file path.
    """
    if dataset is None:
        dataset = generate_dataset(seed=seed)

    out = Path(output_dir) if output_dir else CSV_DIR
    out.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}
    for table in TABLE_ORDER:
        rows = dataset[table]
        path = out / f"{table}.csv"
        df = pd.DataFrame(rows)
        df.to_csv(path, index=False)
        written[table] = path
    return written


def main() -> None:
    dataset = generate_dataset()
    paths = export_dataset_to_csv(dataset)
    print("CSV export complete:")
    for table, path in paths.items():
        print(f"  {table}: {path} ({summarize_dataset(dataset)[table]} rows)")


if __name__ == "__main__":
    main()
