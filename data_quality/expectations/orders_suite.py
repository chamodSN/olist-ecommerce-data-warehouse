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
    data_source = context.data_sources.add_pandas("orders_pandas_ds")
    data_asset = data_source.add_dataframe_asset(name="orders_asset")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("orders_batch_def")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    suite = gx.ExpectationSuite(name="orders_suite")
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="order_id"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeUnique(column="order_id"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="order_purchase_timestamp"))
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(column="order_status", value_set=KNOWN_ORDER_STATUSES)
    )

    # Nulls ARE expected here (identified using recon notebook)
    # so i used an upper bound on the null rate instead of "never null." 
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(
            column="order_approved_at", mostly=0.997  # ~99.7% non-null
        )
    )

    results = batch.validate(suite)
    print(f"Orders validation success: {results.success}")
    return results


if __name__ == "__main__":
    validate_orders()