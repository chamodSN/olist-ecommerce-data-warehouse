import great_expectations as gx
import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

KNOWN_ORDER_STATUSES = [
    "delivered", "shipped", "canceled", "invoiced",
    "processing", "created", "approved", "unavailable",
]


def validate_orders():
    df = pd.read_csv(RAW_DIR / "olist_orders_dataset.csv")

    context = gx.get_context()
    validator = context.sources.pandas_default.read_dataframe(df)

    validator.expect_column_values_to_not_be_null("order_id")
    validator.expect_column_values_to_be_unique("order_id")
    validator.expect_column_values_to_not_be_null("order_purchase_timestamp")
    validator.expect_column_values_to_be_in_set("order_status", KNOWN_ORDER_STATUSES)

    # Nulls ARE expected here (identified using recon notebook)
    # so i used an upper bound on the null rate instead of "never null." 
    validator.expect_column_values_to_not_be_null(
        "order_approved_at", mostly=0.997  # ~99.7% non-null
    )

    results = validator.validate()
    print(f"Orders validation success: {results.success}")
    return results


if __name__ == "__main__":
    validate_orders()