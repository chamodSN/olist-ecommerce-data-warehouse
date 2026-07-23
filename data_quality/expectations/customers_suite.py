import great_expectations as gx
import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def validate_customers():
    df = pd.read_csv(RAW_DIR / "olist_customers_dataset.csv")

    context = gx.get_context()
    
    data_source = context.data_sources.add_pandas("customers_pandas_ds")
    data_asset = data_source.add_dataframe_asset(name="customers_asset")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("customers_batch_def")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    suite = gx.ExpectationSuite(name="customers_suite")
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="customer_id"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeUnique(column="customer_id"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="customer_unique_id"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="customer_state"))
    suite.add_expectation(gx.expectations.ExpectColumnValueLengthsToEqual(column="customer_state", value=2))

    results = batch.validate(suite)

    print(f"Customers validation success: {results.success}")
    return results


if __name__ == "__main__":
    validate_customers()