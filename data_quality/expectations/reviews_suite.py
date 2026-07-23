import great_expectations as gx
import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def validate_reviews():
    df = pd.read_csv(RAW_DIR / "olist_order_reviews_dataset.csv")

    context = gx.get_context()
    validator = context.sources.pandas_default.read_dataframe(df)

    validator.expect_column_values_to_not_be_null("review_id")
    validator.expect_column_values_to_not_be_null("order_id")
    validator.expect_column_values_to_be_between("review_score", min_value=1, max_value=5)

    # From the recon notebook: review_id is NOT globally unique
    # Instead i have assert the compound key is unique.
    validator.expect_compound_columns_to_be_unique(["review_id", "order_id"])

    results = validator.validate()
    print(f"Reviews validation success: {results.success}")
    return results


if __name__ == "__main__":
    validate_reviews()