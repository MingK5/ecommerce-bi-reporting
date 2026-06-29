"""
Load processed Olist BI CSV files into PostgreSQL.

Run from project root:
    python etl/load_to_postgres.py

Before running:
1. Create a PostgreSQL database, e.g. bi_dashboard
2. Copy .env.example to .env and update your DB password
3. Run build_processed_data.py first so data/processed/*.csv exists
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# Allow importing config.py from project root when script runs from etl/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from config import DATABASE_URL, PROCESSED_DIR, SQL_DIR  # noqa: E402


TABLE_LOAD_ORDER = [
    "dim_customer",
    "dim_product",
    "dim_seller",
    "dim_geolocation",
    "dim_date",
    "fact_orders",
    "fact_order_items",
    "fact_payments",
    "fact_reviews",
    "monthly_kpis",
    "top_sellers_monthly",
    "top_products_monthly",
]

DATE_COLUMNS = {
    "dim_date": ["date"],
    "fact_orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "purchase_date",
    ],
    "fact_order_items": ["shipping_limit_date"],
    "fact_reviews": ["review_creation_date", "review_answer_timestamp"],
}


def read_processed_csv(table_name: str) -> pd.DataFrame:
    csv_path = PROCESSED_DIR / f"{table_name}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing processed CSV: {csv_path}")

    df = pd.read_csv(csv_path)

    for col in DATE_COLUMNS.get(table_name, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df


def run_schema(engine) -> None:
    schema_path = SQL_DIR / "create_tables.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Missing SQL schema file: {schema_path}")

    sql = schema_path.read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.execute(text(sql))


def load_table(engine, table_name: str) -> None:
    df = read_processed_csv(table_name)
    print(f"Loading {table_name}: {len(df):,} rows")

    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=5000,
        method="multi",
    )


def main() -> None:
    print("Connecting to PostgreSQL...")
    engine = create_engine(DATABASE_URL)

    print("Creating tables...")
    run_schema(engine)

    for table in TABLE_LOAD_ORDER:
        load_table(engine, table)

    print("\nDone. PostgreSQL database is ready for Power BI and Excel VBA.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        sys.exit(1)
