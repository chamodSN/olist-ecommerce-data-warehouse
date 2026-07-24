import pandas as pd
from common import read_latest_bronze_csv, write_silver_parquet


DATE_COLUMNS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]


def transform_orders():
    df = read_latest_bronze_csv("orders", "olist_orders_dataset.csv")

    for col in DATE_COLUMNS:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    df["order_status"] = df["order_status"].str.lower().str.strip()

    df["is_delivered"] = df["order_status"] == "delivered"

    df["delivery_delay_days"] = (
        df["order_delivered_customer_date"] -
        df["order_estimated_delivery_date"]
    ).dt.days

    write_silver_parquet(df, "orders")
    return df


if __name__ == "__main__":
    transform_orders()
