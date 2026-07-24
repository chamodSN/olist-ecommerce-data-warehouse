from common import read_latest_bronze_csv, write_silver_parquet, strip_accents


def transform_sellers():
    df = read_latest_bronze_csv("sellers", "olist_sellers_dataset.csv")

    df["seller_city"] = df["seller_city"].apply(
        strip_accents).str.lower().str.strip()
    df["seller_state"] = df["seller_state"].str.upper().str.strip()
    df["seller_zip_code_prefix"] = df["seller_zip_code_prefix"].astype(
        str).str.zfill(5)

    write_silver_parquet(df, "sellers")
    return df


if __name__ == "__main__":
    transform_sellers()
