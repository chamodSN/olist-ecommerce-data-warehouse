"""
Runs all Bronze-layer data quality suites, prints a summary, and builds
the HTML data docs report.

Resets any previous great_expectations/ project folder first, so every
run starts from a clean slate and no suite file needs get-or-add logic
to handle "this already exists from last time" -- see gx_context.py for
the full reasoning.
"""

import shutil
import sys
from pathlib import Path

from data_quality.expectations.customers_suite import validate_customers
from data_quality.expectations.orders_suite import validate_orders
from data_quality.expectations.order_items_suite import validate_order_items
from data_quality.expectations.reviews_suite import validate_reviews


def reset_gx_project():
    gx_project_dir = Path(__file__).resolve().parent / "great_expectations"
    if gx_project_dir.exists():
        shutil.rmtree(gx_project_dir)


def main():
    reset_gx_project()

    checks = {
        "customers": validate_customers,
        "orders": validate_orders,
        "order_items": validate_order_items,
        "reviews": validate_reviews,
    }

    results = {}
    context = None

    for name, check_fn in checks.items():
        print(f"Running data quality check: {name}")
        result, context = check_fn()
        results[name] = result.success  # .success specifically -- the raw
        # result object is always truthy regardless of pass/fail, which
        # was silently making every summary line print PASS before.

    print("\n--- Summary ---")
    all_passed = True
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    if context is not None:
        context.build_data_docs()
        print("\nData docs built. Open great_expectations/uncommitted/data_docs/local_site/index.html")

    if not all_passed:
        print("\nOne or more data quality checks failed.")
        sys.exit(1)

    print("\nAll data quality checks passed.")


if __name__ == "__main__":
    main()
