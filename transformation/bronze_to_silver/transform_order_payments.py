from common import read_latest_bronze_csv, write_silver_parquet


def transform_order_payments():
    df = read_latest_bronze_csv(
        "order_payments", "olist_order_payments_dataset.csv")

    df["payment_type"] = df["payment_type"].str.lower().str.strip()
    df["payment_value"] = df["payment_value"].astype(float)
    df["payment_installments"] = df["payment_installments"].astype(int)

    write_silver_parquet(df, "order_payments")
    return df


if __name__ == "__main__":
    transform_order_payments()
