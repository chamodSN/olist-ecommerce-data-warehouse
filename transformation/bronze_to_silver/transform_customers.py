from common import read_latest_bronze_csv, logger, strip_accents, write_silver_parquet


def transform_customers():

    df = read_latest_bronze_csv("customers", "olist_customers_dataset.csv")

    df["customer_city"] = df["customer_city"].apply(
        strip_accents).str.lower().str.strip()

    df["customer_state"] = df["customer_state"].str.upper().str.strip()

    df["customer_zip_code_prefix"] = df["customer_zip_code_prefix"].astype(
        str).str.zfill(5)

    row_count_before = len(df)
    df = df.drop_duplicates(subset=["customer_id"])
    if len(df) != row_count_before:
        logger.warning(
            f"Dropped {row_count_before - len(df)} duplicate customer_id rows")

    write_silver_parquet(df, "customers")

    return df


if __name__ == "__main__":
    transform_customers()
