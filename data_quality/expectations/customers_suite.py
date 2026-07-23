import great_expectations as gx
from pathlib import Path
import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[2]/"data"/"raw"

def validate_customers():
    df = pd.read_csv(RAW_DIR/"olist_customers_dataset.csv")

    context = gx.get_context()

    validator = context.sources.pandas_default.read_dataframe(df)

    validator.expect_column_values_to_not_be_null("customer_id")
    validator.expect_column_values_to_be_unique("customer_id")
    validator.expect_column_values_to_not_be_null("customer_unique_id")
    validator.expect_column_values_to_not_be_null("customer_state")
    validator.expect_column_value_lengths_to_equal("customer_state", 2)

    results = validator.validate()

    print(f"Customers validation success: {results.success}")
    return results

if __name__ == "__main__":
    validate_customers()