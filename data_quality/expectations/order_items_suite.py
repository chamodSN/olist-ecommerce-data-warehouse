import great_expectations as gx
import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def validate_order_items():
    df = pd.read_csv(RAW_DIR / "olist_order_items_dataset.csv")

    context = gx.get_context()
    data_source = context.data_sources.add_pandas("order_items_pandas_ds")
    data_asset = data_source.add_dataframe_asset(name="order_items_asset")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("order_items_batch_def")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    suite = gx.ExpectationSuite(name="order_items_suite")
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="order_id"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="product_id"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="price", min_value=0))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="freight_value", min_value=0))
    suite.add_expectation(
        gx.expectations.ExpectCompoundColumnsToBeUnique(column_list=["order_id", "order_item_id"])
    )

    results = batch.validate(suite)
    print(f"Order items validation success: {results.success}")
    return results


if __name__ == "__main__":
    validate_order_items()