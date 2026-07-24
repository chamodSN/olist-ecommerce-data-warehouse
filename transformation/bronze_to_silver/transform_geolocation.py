from common import read_latest_bronze_csv, write_silver_parquet, strip_accents, logger


def transform_geolocation():
    df = read_latest_bronze_csv("geolocation", "olist_geolocation_dataset.csv")

    df["geolocation_city"] = df["geolocation_city"].apply(strip_accents).str.lower().str.strip()
    df["geolocation_state"] = df["geolocation_state"].str.upper().str.strip()
    df["geolocation_zip_code_prefix"] = df["geolocation_zip_code_prefix"].astype(str).str.zfill(5)

    before = len(df)
    df = df[
        (df["geolocation_lat"].between(-34, 6)) &
        (df["geolocation_lng"].between(-74, -32))
    ]
    logger.info(f"Filtered {before - len(df)} rows outside Brazil's coordinate range")

    agg = (
        df.groupby("geolocation_zip_code_prefix")
        .agg(
            geolocation_lat=("geolocation_lat", "mean"),
            geolocation_lng=("geolocation_lng", "mean"),
            geolocation_city=("geolocation_city", lambda x: x.mode().iloc[0]),
            geolocation_state=("geolocation_state", lambda x: x.mode().iloc[0]),
        )
        .reset_index()
    )

    logger.info(f"Aggregated {len(df)} raw rows down to {len(agg)} unique zip prefixes")

    write_silver_parquet(agg, "geolocation")
    return agg


if __name__ == "__main__":
    transform_geolocation()