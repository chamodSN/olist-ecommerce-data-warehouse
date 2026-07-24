import pandas as pd
from common import read_latest_bronze_csv, write_silver_parquet


def transform_order_items():
    df = read_latest_bronze_csv("order_items", "olist_order_items_dataset.csv")

    df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"], errors="coerce")
    df["price"] = df["price"].astype(float)
    df["freight_value"] = df["freight_value"].astype(float)

    write_silver_parquet(df, "order_items")
    return df


if __name__ == "__main__":
    transform_order_items()