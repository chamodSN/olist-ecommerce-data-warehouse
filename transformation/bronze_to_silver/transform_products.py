from common import read_latest_bronze_csv, write_silver_parquet, logger


def transform_products():
    products = read_latest_bronze_csv("products", "olist_products_dataset.csv")
    translation = read_latest_bronze_csv(
        "category_translation", "product_category_name_translation.csv")

    before_null = products["product_category_name"].isnull().sum()
    products["product_category_name"] = products["product_category_name"].fillna(
        "unknown")
    logger.info(
        f"Filled {before_null} null product_category_name values with 'unknown'")

    merged = products.merge(
        translation, on="product_category_name", how="left")

    missing_translation = merged["product_category_name_english"].isnull(
    ).sum()
    merged["product_category_name_english"] = merged["product_category_name_english"].fillna(
        merged["product_category_name"]
    )
    logger.info(
        f"{missing_translation} products had no English translation; fell back to original name")

    numeric_cols = [
        "product_name_lenght", "product_description_lenght", "product_photos_qty",
        "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm",
    ]
    for col in numeric_cols:
        merged[col] = merged[col].astype(float)

    write_silver_parquet(merged, "products")
    return merged


if __name__ == "__main__":
    transform_products()
