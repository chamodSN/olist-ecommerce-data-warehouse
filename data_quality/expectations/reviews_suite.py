import great_expectations as gx
import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def validate_reviews():
    df = pd.read_csv(RAW_DIR / "olist_order_reviews_dataset.csv")

    context = gx.get_context()
    data_source = context.data_sources.add_pandas("reviews_pandas_ds")
    data_asset = data_source.add_dataframe_asset(name="reviews_asset")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("reviews_batch_def")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    suite = gx.ExpectationSuite(name="reviews_suite")
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="review_id"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="order_id"))
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(column="review_score", min_value=1, max_value=5)
    )

    # From the recon notebook: review_id is NOT globally unique
    # Instead i have assert the compound key is unique.
    suite.add_expectation(
        gx.expectations.ExpectCompoundColumnsToBeUnique(column_list=["review_id", "order_id"])
    )

    results = batch.validate(suite)
    print(f"Reviews validation success: {results.success}")
    return results


if __name__ == "__main__":
    validate_reviews()