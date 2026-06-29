"""
Build processed BI datasets for Olist Logistics Analytics project.

Input folder:
    data/raw/

Output folder:
    data/processed/

Run from project root:
    python etl/build_processed_data.py

This script:
1. Reads raw Olist CSV files.
2. Converts long hash IDs into readable business IDs.
3. Builds dimension and fact CSVs for Power BI.
4. Builds monthly KPI CSVs for Excel VBA reporting.
"""

from __future__ import annotations
from pathlib import Path
import sys
import pandas as pd

PROJECT_ROOT_FOR_IMPORT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT_FOR_IMPORT))

from config import PROJECT_ROOT, RAW_DIR, PROCESSED_DIR


def find_raw_file(keyword: str) -> Path:
    """Find one raw CSV by keyword, allowing filenames with suffixes like (2), (3), etc."""
    matches = sorted(RAW_DIR.glob(f"*{keyword}*.csv"))
    if not matches:
        raise FileNotFoundError(f"Cannot find raw CSV containing keyword: {keyword} in {RAW_DIR}")
    return matches[0]


def read_csv(keyword: str) -> pd.DataFrame:
    path = find_raw_file(keyword)
    print(f"Reading: {path.name}")
    return pd.read_csv(path)


def make_id_lookup(values: pd.Series, prefix: str, width: int = 6) -> pd.DataFrame:
    """Create deterministic original_id -> display_id mapping."""
    unique_values = (
        values.dropna()
        .astype(str)
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )

    return pd.DataFrame({
        "original_id": unique_values,
        "display_id": [
            f"{prefix}-{str(i + 1).zfill(width)}"
            for i in range(len(unique_values))
        ],
    })


def map_ids(df: pd.DataFrame, column: str, lookup: pd.DataFrame, new_column: str) -> pd.DataFrame:
    mapping = dict(zip(lookup["original_id"], lookup["display_id"]))
    df[new_column] = df[column].astype(str).map(mapping)
    return df


def to_datetime(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def to_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Force numeric columns to numeric dtype.

    Some CSV/Excel environments may read numeric columns as object strings.
    This prevents aggregation errors when using mean/sum later.
    """
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def build_date_dimension(date_series: pd.Series) -> pd.DataFrame:
    dates = pd.to_datetime(date_series.dropna(), errors="coerce").dropna()
    if dates.empty:
        return pd.DataFrame()

    start_date = dates.min().date()
    end_date = dates.max().date()

    date_range = pd.date_range(start=start_date, end=end_date, freq="D")

    dim_date = pd.DataFrame({"date": date_range})
    dim_date["date_key"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["quarter"] = "Q" + dim_date["date"].dt.quarter.astype(str)
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["month_name"] = dim_date["date"].dt.month_name()
    dim_date["year_month"] = dim_date["date"].dt.strftime("%Y-%m")
    dim_date["day"] = dim_date["date"].dt.day
    dim_date["day_name"] = dim_date["date"].dt.day_name()
    dim_date["week_of_year"] = dim_date["date"].dt.isocalendar().week.astype(int)
    dim_date["is_weekend"] = dim_date["date"].dt.dayofweek >= 5
    dim_date["date"] = dim_date["date"].dt.date.astype(str)

    return dim_date


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------------
    # 1. Load raw data
    # -----------------------------
    customers = read_csv("customers")
    geolocation = read_csv("geolocation")
    order_items = read_csv("order_items")
    payments = read_csv("order_payments")
    reviews = read_csv("order_reviews")
    orders = read_csv("orders")
    products = read_csv("products")
    sellers = read_csv("sellers")
    category_translation = read_csv("product_category_name_translation")

    # -----------------------------
    # 1B. Force important numeric columns
    # -----------------------------
    customers = to_numeric(customers, ["customer_zip_code_prefix"])
    geolocation = to_numeric(geolocation, [
        "geolocation_zip_code_prefix",
        "geolocation_lat",
        "geolocation_lng",
    ])
    order_items = to_numeric(order_items, [
        "order_item_id",
        "price",
        "freight_value",
    ])
    payments = to_numeric(payments, [
        "payment_sequential",
        "payment_installments",
        "payment_value",
    ])
    reviews = to_numeric(reviews, ["review_score"])
    products = to_numeric(products, [
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ])
    sellers = to_numeric(sellers, ["seller_zip_code_prefix"])

    # -----------------------------
    # 2. Create readable ID lookups
    # -----------------------------
    order_ids = pd.concat([
        orders["order_id"],
        order_items["order_id"],
        payments["order_id"],
        reviews["order_id"],
    ], ignore_index=True)

    customer_ids = customers["customer_id"]
    customer_unique_ids = customers["customer_unique_id"]

    product_ids = pd.concat([
        products["product_id"],
        order_items["product_id"],
    ], ignore_index=True)

    seller_ids = pd.concat([
        sellers["seller_id"],
        order_items["seller_id"],
    ], ignore_index=True)

    review_ids = reviews["review_id"]

    order_lookup = make_id_lookup(order_ids, "ORD")
    customer_lookup = make_id_lookup(customer_ids, "CUST")
    customer_unique_lookup = make_id_lookup(customer_unique_ids, "UCUST")
    product_lookup = make_id_lookup(product_ids, "PROD")
    seller_lookup = make_id_lookup(seller_ids, "SELL")
    review_lookup = make_id_lookup(review_ids, "REV")

    order_lookup.to_csv(PROCESSED_DIR / "lookup_order_ids.csv", index=False)
    customer_lookup.to_csv(PROCESSED_DIR / "lookup_customer_ids.csv", index=False)
    customer_unique_lookup.to_csv(PROCESSED_DIR / "lookup_customer_unique_ids.csv", index=False)
    product_lookup.to_csv(PROCESSED_DIR / "lookup_product_ids.csv", index=False)
    seller_lookup.to_csv(PROCESSED_DIR / "lookup_seller_ids.csv", index=False)
    review_lookup.to_csv(PROCESSED_DIR / "lookup_review_ids.csv", index=False)

    # -----------------------------
    # 3. Apply readable IDs
    # -----------------------------
    orders = map_ids(orders, "order_id", order_lookup, "order_display_id")
    orders = map_ids(orders, "customer_id", customer_lookup, "customer_display_id")

    customers = map_ids(customers, "customer_id", customer_lookup, "customer_display_id")
    customers = map_ids(customers, "customer_unique_id", customer_unique_lookup, "customer_unique_display_id")

    order_items = map_ids(order_items, "order_id", order_lookup, "order_display_id")
    order_items = map_ids(order_items, "product_id", product_lookup, "product_display_id")
    order_items = map_ids(order_items, "seller_id", seller_lookup, "seller_display_id")

    payments = map_ids(payments, "order_id", order_lookup, "order_display_id")

    reviews = map_ids(reviews, "order_id", order_lookup, "order_display_id")
    reviews = map_ids(reviews, "review_id", review_lookup, "review_display_id")

    products = map_ids(products, "product_id", product_lookup, "product_display_id")

    sellers = map_ids(sellers, "seller_id", seller_lookup, "seller_display_id")

    # -----------------------------
    # 4. Clean dates
    # -----------------------------
    orders = to_datetime(orders, [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ])

    order_items = to_datetime(order_items, ["shipping_limit_date"])
    reviews = to_datetime(reviews, ["review_creation_date", "review_answer_timestamp"])

    # -----------------------------
    # 5. Build dimension tables
    # -----------------------------
    dim_customer = customers[[
        "customer_display_id",
        "customer_unique_display_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
        "customer_id",
        "customer_unique_id",
    ]].rename(columns={
        "customer_zip_code_prefix": "zip_code_prefix",
        "customer_city": "city",
        "customer_state": "state",
        "customer_id": "original_customer_id",
        "customer_unique_id": "original_customer_unique_id",
    })

    dim_product = products.merge(
        category_translation,
        on="product_category_name",
        how="left"
    )

    dim_product["product_category_name_english"] = dim_product["product_category_name_english"].fillna("unknown")

    dim_product = dim_product[[
        "product_display_id",
        "product_category_name",
        "product_category_name_english",
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
        "product_id",
    ]].rename(columns={
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length",
        "product_id": "original_product_id",
    })

    dim_seller = sellers[[
        "seller_display_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state",
        "seller_id",
    ]].rename(columns={
        "seller_zip_code_prefix": "zip_code_prefix",
        "seller_city": "city",
        "seller_state": "state",
        "seller_id": "original_seller_id",
    })

    # Geolocation has duplicate zip rows, so aggregate to one row per zip/state/city.
    dim_geolocation = (
        geolocation
        .groupby(["geolocation_zip_code_prefix", "geolocation_city", "geolocation_state"], as_index=False)
        .agg(
            avg_lat=("geolocation_lat", "mean"),
            avg_lng=("geolocation_lng", "mean"),
        )
        .rename(columns={
            "geolocation_zip_code_prefix": "zip_code_prefix",
            "geolocation_city": "city",
            "geolocation_state": "state",
        })
    )

    all_dates = pd.concat([
        orders["order_purchase_timestamp"],
        orders["order_approved_at"],
        orders["order_delivered_carrier_date"],
        orders["order_delivered_customer_date"],
        orders["order_estimated_delivery_date"],
        order_items["shipping_limit_date"],
        reviews["review_creation_date"],
        reviews["review_answer_timestamp"],
    ], ignore_index=True)

    dim_date = build_date_dimension(all_dates)

    # -----------------------------
    # 6. Build fact tables
    # -----------------------------
    fact_orders = orders[[
        "order_display_id",
        "customer_display_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "order_id",
        "customer_id",
    ]].rename(columns={
        "order_id": "original_order_id",
        "customer_id": "original_customer_id",
    })

    fact_orders["purchase_date"] = fact_orders["order_purchase_timestamp"].dt.date.astype("string")
    fact_orders["purchase_year_month"] = fact_orders["order_purchase_timestamp"].dt.strftime("%Y-%m")
    fact_orders["delivery_days"] = (
        fact_orders["order_delivered_customer_date"] -
        fact_orders["order_purchase_timestamp"]
    ).dt.days
    fact_orders["late_delivery_days"] = (
        fact_orders["order_delivered_customer_date"] -
        fact_orders["order_estimated_delivery_date"]
    ).dt.days
    fact_orders["is_late_delivery"] = fact_orders["late_delivery_days"].fillna(0).gt(0).astype(int)

    fact_order_items = order_items[[
        "order_display_id",
        "order_item_id",
        "product_display_id",
        "seller_display_id",
        "shipping_limit_date",
        "price",
        "freight_value",
        "order_id",
        "product_id",
        "seller_id",
    ]].rename(columns={
        "order_id": "original_order_id",
        "product_id": "original_product_id",
        "seller_id": "original_seller_id",
    })

    fact_order_items["item_revenue"] = fact_order_items["price"] + fact_order_items["freight_value"]

    fact_payments = payments[[
        "order_display_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value",
        "order_id",
    ]].rename(columns={
        "order_id": "original_order_id",
    })

    fact_reviews = reviews[[
        "review_display_id",
        "order_display_id",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp",
        "review_id",
        "order_id",
    ]].rename(columns={
        "review_id": "original_review_id",
        "order_id": "original_order_id",
    })

    # -----------------------------
    # 7. Build reporting tables for Excel VBA
    # -----------------------------
    payment_per_order = (
        fact_payments
        .groupby("order_display_id", as_index=False)
        .agg(total_revenue=("payment_value", "sum"))
    )

    order_report_base = (
        fact_orders
        .merge(payment_per_order, on="order_display_id", how="left")
        .merge(dim_customer[["customer_display_id", "customer_unique_display_id"]], on="customer_display_id", how="left")
    )

    order_report_base["total_revenue"] = order_report_base["total_revenue"].fillna(0)

    monthly_kpis = (
        order_report_base
        .dropna(subset=["purchase_year_month"])
        .groupby("purchase_year_month", as_index=False)
        .agg(
            revenue=("total_revenue", "sum"),
            orders=("order_display_id", "nunique"),
            unique_customers=("customer_unique_display_id", "nunique"),
            late_deliveries=("is_late_delivery", "sum"),
            delivered_orders=("order_delivered_customer_date", lambda s: s.notna().sum()),
            avg_delivery_days=("delivery_days", "mean"),
        )
    )

    monthly_kpis["late_delivery_pct"] = monthly_kpis.apply(
        lambda row: (row["late_deliveries"] / row["delivered_orders"] * 100)
        if row["delivered_orders"] else 0,
        axis=1,
    ).round(2)

    monthly_kpis["avg_delivery_days"] = monthly_kpis["avg_delivery_days"].round(2)
    monthly_kpis["revenue"] = monthly_kpis["revenue"].round(2)

    items_with_month = fact_order_items.merge(
        fact_orders[["order_display_id", "purchase_year_month"]],
        on="order_display_id",
        how="left",
    )

    top_sellers_monthly = (
        items_with_month
        .dropna(subset=["purchase_year_month"])
        .groupby(["purchase_year_month", "seller_display_id"], as_index=False)
        .agg(
            revenue=("item_revenue", "sum"),
            orders=("order_display_id", "nunique"),
            units_sold=("order_item_id", "count"),
        )
        .sort_values(["purchase_year_month", "revenue"], ascending=[True, False])
    )

    top_sellers_monthly["revenue"] = top_sellers_monthly["revenue"].round(2)

    product_lookup_for_report = dim_product[[
        "product_display_id",
        "product_category_name_english",
    ]]

    product_monthly_base = items_with_month.merge(
        product_lookup_for_report,
        on="product_display_id",
        how="left",
    )

    top_products_monthly = (
        product_monthly_base
        .dropna(subset=["purchase_year_month"])
        .groupby(["purchase_year_month", "product_display_id", "product_category_name_english"], as_index=False)
        .agg(
            revenue=("item_revenue", "sum"),
            orders=("order_display_id", "nunique"),
            units_sold=("order_item_id", "count"),
        )
        .sort_values(["purchase_year_month", "revenue"], ascending=[True, False])
    )

    top_products_monthly["revenue"] = top_products_monthly["revenue"].round(2)

    # -----------------------------
    # 8. Save outputs
    # -----------------------------
    outputs = {
        "dim_customer.csv": dim_customer,
        "dim_product.csv": dim_product,
        "dim_seller.csv": dim_seller,
        "dim_geolocation.csv": dim_geolocation,
        "dim_date.csv": dim_date,
        "fact_orders.csv": fact_orders,
        "fact_order_items.csv": fact_order_items,
        "fact_payments.csv": fact_payments,
        "fact_reviews.csv": fact_reviews,
        "monthly_kpis.csv": monthly_kpis,
        "top_sellers_monthly.csv": top_sellers_monthly,
        "top_products_monthly.csv": top_products_monthly,
    }

    for filename, df in outputs.items():
        output_path = PROCESSED_DIR / filename
        df.to_csv(output_path, index=False)
        print(f"Saved: {output_path.relative_to(PROJECT_ROOT)} ({len(df):,} rows)")

    print("\nDone. Processed files are ready for Power BI and Excel VBA.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        sys.exit(1)
