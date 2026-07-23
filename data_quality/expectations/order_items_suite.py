import great_expectations as gx
import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def validate_order_items():
    df = pd.read_csv(RAW_DIR / "olist_order_items_dataset.csv")

    context = gx.get_context()
    validator = context.sources.pandas_default.read_dataframe(df)

    validator.expect_column_values_to_not_be_null("order_id")
    validator.expect_column_values_to_not_be_null("product_id")
    validator.expect_column_values_to_be_between("price", min_value=0)
    validator.expect_column_values_to_be_between("freight_value", min_value=0)
    validator.expect_compound_columns_to_be_unique(["order_id", "order_item_id"])

    results = validator.validate()
    print(f"Order items validation success: {results.success}")
    return results


if __name__ == "__main__":
    validate_order_items()