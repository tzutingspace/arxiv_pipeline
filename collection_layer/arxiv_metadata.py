import logging
import os
from typing import Any

import boto3
from dotenv import load_dotenv
from google.cloud import storage
from utils.format_time import datetime_to_timestamp

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_FOLDER_PREFIX = os.getenv("S3_FOLDER_PREFIX")

SOURCE_GCS_BUCKET_NAME = "arxiv-dataset"
SOURCE_GCS_OBJECT_NAME = "metadata-v5/arxiv-metadata-oai.json"


def lambda_handler(event, context):
    # 1. 確認當下 S3 的最新檔案的詳細資料
    latest_file = get_latest_file_from_s3(S3_BUCKET_NAME, S3_FOLDER_PREFIX)
    latest_file_update_timestamp = latest_file["upload_timestamp"]
    logger.info(f"latest file detail info: {latest_file}")

    # 2. 確認來源的 metadata.json 的版本號
    file_info = get_gcs_object_info(SOURCE_GCS_BUCKET_NAME, SOURCE_GCS_OBJECT_NAME)
    source_file_update_timestamp = file_info["update_time"]
    logger.info(f"source file detail info: {file_info}")

    # 3. 如果來源的版本號比當下 S3 的版本號相同，則跳過
    if int(source_file_update_timestamp) == int(latest_file_update_timestamp):
        logger.info("source file is up to date")
        return

    # 4. 下載最新的 metadata.json 並且直接先上傳至 S3
    source_file_bytes = download_as_bytes_from_gcs(SOURCE_GCS_BUCKET_NAME, SOURCE_GCS_OBJECT_NAME)
    new_file_name = f"{S3_FOLDER_PREFIX}-{source_file_update_timestamp}.json"
    upload_to_s3(S3_BUCKET_NAME, new_file_name, source_file_bytes)


def get_latest_file_from_s3(bucket_name: str, folder_prefix: str) -> dict[str, Any]:
    """
    取得 S3 資料夾中最新檔案名稱
    """
    s3 = boto3.client("s3")

    # 列出資料夾中的所有檔案
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_prefix)

    # 找出最新的檔案
    latest_file = max(response["Contents"], key=lambda x: x["LastModified"])

    # 取得最新檔案的詳細資訊
    # file_details = s3.head_object(Bucket=bucket_name, Key=latest_file["Key"])
    try:
        latest_file_name = latest_file["Key"]
        upload_timestamp = latest_file_name.split("-")[-1].split(".")[0]
    except Exception as e:
        logger.error(e)
        raise e

    return {
        "file_name": latest_file_name,
        "upload_timestamp": upload_timestamp,
    }


def get_gcs_object_info(bucket_name: str, object_name: str) -> dict[str, Any]:
    """
    取得 GCS 物件的詳細資訊，類似 gsutil ls -L 的輸出
    """
    client = storage.Client.create_anonymous_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)

    blob.reload()  # 重新載入以取得最新的 metadata

    return {
        "gs_url": f"gs://{bucket_name}/{object_name}",
        "creation_time": datetime_to_timestamp(blob.time_created),
        "update_time": datetime_to_timestamp(blob.updated),
        "size": blob.size,
        "md5_hash": blob.md5_hash,
        "crc32c_hash": blob.crc32c,
        "etag": blob.etag,
        "generation": blob.generation,
        "metageneration": blob.metageneration,
    }


def download_as_bytes_from_gcs(bucket_name: str, object_name: str) -> bytes:
    client = storage.Client.create_anonymous_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    return blob.download_as_bytes()


def upload_to_s3(bucket_name: str, object_name: str, file_bytes: bytes) -> None:
    s3 = boto3.client("s3")
    s3.put_object(Bucket=bucket_name, Key=object_name, Body=file_bytes)


if __name__ == "__main__":
    lambda_handler(None, None)
