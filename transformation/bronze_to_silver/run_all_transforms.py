import logging

from transform_customers import transform_customers
from transform_geolocation import transform_geolocation
from transform_orders import transform_orders
from transform_order_items import transform_order_items
from transform_order_payments import transform_order_payments
from transform_order_reviews import transform_order_reviews
from transform_products import transform_products
from transform_sellers import transform_sellers

logger = logging.getLogger(__name__)


def main():
    transforms = {
        "customers": transform_customers,
        "geolocation": transform_geolocation,
        "orders": transform_orders,
        "order_items": transform_order_items,
        "order_payments": transform_order_payments,
        "order_reviews": transform_order_reviews,
        "products": transform_products,
        "sellers": transform_sellers,
    }

    row_counts = {}
    for name, fn in transforms.items():
        print(f"\nTransforming: {name}")
        df = fn()
        row_counts[name] = len(df)

    print("\n--- Silver row counts ---")
    for name, count in row_counts.items():
        print(f"{name}: {count}")


if __name__ == "__main__":
    main()
