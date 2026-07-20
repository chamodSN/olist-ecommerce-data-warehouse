import boto3
import os
import logging
import sys

from pathlib import Path
from dotenv import load_dotenv
from botocore.exceptions import ClientError, NoCredentialsError

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)

S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
AWS_REGION = os.getenv('AWS_REGION', 'ap-southeast-2')

if not S3_BUCKET_NAME:
    logger.error("S3_BUCKET_NAME is not set in the environment variables.")
    sys.exit(1)

FILE_TO_ENTITY_MAP = {
    "olist_customers_dataset.csv": "customers",
    "olist_geolocation_dataset.csv": "geolocation",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_orders_dataset.csv": "orders",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "product_category_name_translation.csv": "product_category_name_translation",
}

RAW_DIR = Path(__file__).resolve().parents[2] / 'data' / 'raw'


def get_s3_client():
    try:
        client = boto3.client('s3', region_name=AWS_REGION)
        client.list_buckets()
        return client
    except NoCredentialsError:
        logger.error(
            "AWS credentials not found. Please set them in the environment variables.")
        sys.exit(1)


def upload_file(client, local_path: Path, entity: str):
    s3_key = f"raw/olist/{entity}/{local_path.name}"
    try:
        client.upload(str(local_path), S3_BUCKET_NAME, s3_key)
        logger.info(f"Uploaded {local_path} to s3://{S3_BUCKET_NAME}/{s3_key}")
    except ClientError as e:
        logger.error(f"Failed to upload {local_path} to S3: {e}")
        raise


def main():
    if not RAW_DIR.exists():
        logger.error(f"Raw data directory {RAW_DIR} does not exist.")
        sys.exit(1)

    client = get_s3_client()

    missing_files = []
    for file_name, entity in FILE_TO_ENTITY_MAP.items():
        local_path = RAW_DIR/file_name
        if not local_path.exists():
            logger.warning(
                f"File {local_path} does not exist. Skipping upload.")
            missing_files.append(file_name)
            continue
        upload_file(client, local_path, entity)

    if missing_files:
        logger.error(f"The following files are missing: {missing_files}")

    logger.info("Upload process completed.")


if __name__ == "__main__":
    main()
