import pandas as pd
from common import read_latest_bronze_csv, write_silver_parquet


def transform_order_reviews():
    df = read_latest_bronze_csv(
        "order_reviews", "olist_order_reviews_dataset.csv")

    df["review_creation_date"] = pd.to_datetime(
        df["review_creation_date"], errors="coerce")
    df["review_answer_timestamp"] = pd.to_datetime(
        df["review_answer_timestamp"], errors="coerce")
    df["review_score"] = df["review_score"].astype(int)

    write_silver_parquet(df, "order_reviews")
    return df


if __name__ == "__main__":
    transform_order_reviews()
