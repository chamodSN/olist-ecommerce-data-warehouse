import logging
import os

import pandas as pd
import boto3
from dotenv import load_dotenv
from pprint import pprint

import unicodedata

load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BRONZE_BUCKET_NAME = os.getenv("BRONZE_BUCKET_NAME")
SILVER_BUCKET_NAME = os.getenv("SILVER_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")

s3_client = boto3.client('s3', region_name=AWS_REGION)


def read_latest_bronze_csv(entity: str, filename: str) -> pd.DataFrame:

    prefix = f"{entity}/"

    response = s3_client.list_objects_v2(
        Bucket=BRONZE_BUCKET_NAME, Prefix=prefix)

    if 'Contents' not in response:
        raise FileNotFoundError(
            f"No objects found under s3://{BRONZE_BUCKET_NAME}/{prefix}")

    dated_keys = [obj['Key']
                  for obj in response['Contents'] if obj['Key'].endswith(filename)]

    latest_key = sorted(dated_keys)[-1]

    s3_uri = f"s3://{BRONZE_BUCKET_NAME}/{latest_key}"

    return pd.read_csv(s3_uri)


def write_silver_parquet(df: pd.DataFrame, entity: str) -> str:

    s3_key = f"{entity}/{entity}.parquet"
    s3_uri = f"s3://{SILVER_BUCKET_NAME}/{s3_key}"

    df.to_parquet(
        s3_uri,
        engine="pyarrow",
        compression="snappy",
        index=False
    )

    logger.info(
        f"Wrote {len(df)} rows to {s3_uri}"
    )

    return s3_uri


def strip_accents(text: str) -> str:
    if pd.isna(text):
        return text
    normalized_text = unicodedata.normalize('NFKD', str(text))
    return "".join(c for c in normalized_text if not unicodedata.combining(c))
