import sys

from expectations.customers_suite import validate_customers
from expectations.orders_suite import validate_orders
from expectations.order_items_suite import validate_order_items
from expectations.reviews_suite import validate_reviews

def main():

    checks = {
        "customers": validate_customers,
        "orders": validate_orders,
        "order_items": validate_order_items,
        "reviews": validate_reviews
    }

    results = {}
    for name, check_fn in checks.items():
        print(f"Running data quality check: {name}")
        result = check_fn()
        results[name] = result

    print("\n--- Summary ---")
    all_passed = True
    for name, passed in results.items():
        status="PASS" if passed else "FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    if not all_passed:
        print("\nOne or more data quality checks failed.")
        sys.exit(1)

    print("\nAll data quality checks passed.")


if __name__ == "__main__":
    main()