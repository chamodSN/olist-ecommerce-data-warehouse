import boto3
import csv
import json
import logging
import os
import sys

from datetime import date, datetime, timezone
from pathlib import Path

from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# Configs

BRONZE_BUCKET_NAME = os.getenv("BRONZE_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")

INGESTION_DATE = date.today().isoformat()

RAW_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "raw"
)

# File-to-Entity Mapping
FILE_TO_ENTITY_MAP = {
    "olist_customers_dataset.csv": "customers",
    "olist_geolocation_dataset.csv": "geolocation",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_orders_dataset.csv": "orders",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "product_category_name_translation.csv": "category_translation",
}

if not BRONZE_BUCKET_NAME:
    logger.error(
        "Could not resolve BRONZE_BUCKET_NAME. "
        "Please ensure it is set in the .env file or as an environment variable."
    )
    sys.exit(1)


def get_s3_client():
    """
    Creates and returns an S3 client.
    """
    return boto3.client("s3", region_name=AWS_REGION)


def count_csv_rows(local_path: Path) -> int:
    """Counts the number of data rows in a CSV file, excluding the header."""
    with local_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        next(reader, None)  # skip header
        return sum(1 for _ in reader)


def get_file_size(local_path: Path) -> int:
    """Returns the file size in bytes."""
    return local_path.stat().st_size


def upload_file(s3_client, local_path: Path, entity: str) -> dict:
    """
    Uploads a single CSV file to the Bronze S3 layer and returns
    ingestion metadata for the manifest.
    """
    s3_key = f"{entity}/ingestion_date={INGESTION_DATE}/{local_path.name}"

    try:
        s3_client.upload_file(str(local_path), BRONZE_BUCKET_NAME, s3_key)

        row_count = count_csv_rows(local_path)
        file_size = get_file_size(local_path)

        upload_record = {
            "table_name": entity,
            "source_file": local_path.name,
            "s3_key": s3_key,
            "row_count": row_count,
            "file_size_bytes": file_size,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "ingestion_date": INGESTION_DATE,
        }

        logger.info(
            f"Uploaded {local_path.name} to "
            f"s3://{BRONZE_BUCKET_NAME}/{s3_key} "
            f"| rows={row_count} | size={file_size} bytes"
        )

        return upload_record

    except NoCredentialsError:
        logger.error(
            "AWS credentials not found or invalid. Confirm AWS_PROFILE "
            "is set to your scoped project profile "
            "and that it has s3:PutObject on this bucket."
        )
        sys.exit(1)

    except ClientError as error:
        logger.error(f"Failed to upload {local_path} to S3: {error}")
        raise


def create_and_upload_manifest(s3_client, manifest: list[dict]):
    """Creates the ingestion manifest locally and uploads it to Bronze."""
    manifest_filename = f"ingestion_manifest_{INGESTION_DATE}.json"
    manifest_path = RAW_DIR / manifest_filename

    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)

    manifest_s3_key = f"_manifests/{manifest_filename}"

    try:
        s3_client.upload_file(str(manifest_path),
                              BRONZE_BUCKET_NAME, manifest_s3_key)
        logger.info(
            f"Manifest uploaded to s3://{BRONZE_BUCKET_NAME}/{manifest_s3_key}")

    except ClientError as error:
        logger.error(f"Failed to upload manifest to S3: {error}")
        raise


def main():
    logger.info(f"Starting Bronze ingestion for {INGESTION_DATE}")
    logger.info(f"Source directory: {RAW_DIR}")
    logger.info(f"Target bucket: {BRONZE_BUCKET_NAME}")

    if not RAW_DIR.exists():
        logger.error(f"Raw data directory does not exist: {RAW_DIR}")
        sys.exit(1)

    s3_client = get_s3_client()

    manifest = []
    missing_files = []

    for file_name, entity in FILE_TO_ENTITY_MAP.items():
        local_path = RAW_DIR / file_name

        if not local_path.exists():
            logger.warning(f"Missing file, skipping: {local_path}")
            missing_files.append(file_name)
            continue

        record = upload_file(s3_client=s3_client,
                             local_path=local_path, entity=entity)
        manifest.append(record)

    if manifest:
        create_and_upload_manifest(s3_client=s3_client, manifest=manifest)

    logger.info(f"Bronze ingestion completed. Uploaded {len(manifest)} files.")

    if missing_files:
        logger.warning(f"Missing files: {missing_files}")


if __name__ == "__main__":
    main()
