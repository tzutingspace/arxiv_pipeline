import json
import logging
import os
import time

import boto3
import pandas as pd
from dotenv import load_dotenv
from utils.format_time import iso_to_timestamp_ms

if "AWS_LAMBDA_FUNCTION_NAME" in os.environ:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
else:
    # 本地環境：使用 basicConfig
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)

load_dotenv()

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_FOLDER_PREFIX = os.getenv("S3_FOLDER_PREFIX")

SOURCE_GCS_BUCKET_NAME = "arxiv-dataset"
SOURCE_GCS_OBJECT_NAME = "metadata-v5/arxiv-metadata-oai.json"


def lambda_handler(event, context):
    logger.info(f"Lambda function started,{event}, {context}")
    # 1. 確認當下 S3 的最新檔案的詳細資料
    latest_file_update_timestamp = get_latest_processed_timestamp()

    # 2. 確認來源的 metadata.json 的最新更新時間
    kaggle_arxiv_metadata_service = ArxivMetadataService()
    latest_update_timestamp = kaggle_arxiv_metadata_service.get_latest_update_time()

    # 3. 如果來源的版本號比當下 S3 的版本號相同，則跳過
    if int(latest_update_timestamp) == int(latest_file_update_timestamp):
        logger.info("source file is up to date")
        return {"status": "skip"}

    # # 4. 下載最新的 metadata.json
    source_file_path = kaggle_arxiv_metadata_service.download_latest_metadata()

    # # 5. 處理 metadata.json 的資料
    process_metadata_json(source_file_path)

    # 6. 上傳最新的 metadata.json 至 S3, 表示已進入下一個流程
    new_file_name = f"{S3_FOLDER_PREFIX}-{latest_update_timestamp}.json"
    # upload_to_s3(S3_BUCKET_NAME, new_file_name, source_file_path)

    return {"status": "success"}


def get_latest_processed_timestamp() -> int:
    s3 = boto3.client("s3")
    response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=S3_FOLDER_PREFIX)
    if "Contents" not in response:
        return 0
    latest_file = max(response["Contents"], key=lambda x: x["LastModified"])
    logger.info(f"latest_processed_file: {latest_file}")
    return latest_file["Key"].split("-")[-1].split(".")[0]


def upload_to_s3(bucket_name: str, object_name: str, file_path: str) -> None:
    s3 = boto3.client("s3")
    s3.upload_file(file_path, bucket_name, object_name)


class ArxivMetadataService:
    def __init__(self):
        self.dataset_ref = "Cornell-University/arxiv"
        self._init_kaggle()

    def _init_kaggle(self):
        # Import kaggle only when needed to avoid undefined errors
        import kaggle

        self.kaggle = kaggle
        self.kaggle.api.authenticate()

    def get_latest_update_time(self) -> int:
        datasets = self.kaggle.api.dataset_list(search=self.dataset_ref)
        dataset_metadata = None

        for dataset in datasets:
            if dataset.ref == self.dataset_ref:
                dataset_metadata = dataset.to_dict()
                break

        if not dataset_metadata:
            raise ValueError(f"Dataset {self.dataset_ref} not found")

        logger.info(f"dataset_metadata: {dataset_metadata}")
        return iso_to_timestamp_ms(dataset_metadata["lastUpdated"])

    def download_latest_metadata(self) -> str:
        tmp_dir = "/tmp"

        st = time.time()
        self.kaggle.api.dataset_download_files(self.dataset_ref, path=tmp_dir, unzip=True)
        logger.info(f"下載並解壓縮檔案花費時間: {time.time() - st:.2f} 秒")

        for _, _, files in os.walk(tmp_dir):
            logger.info(f"找到的檔案: {files}")
            json_files = [f for f in files if f == "arxiv-metadata-oai-snapshot.json"]
            if json_files:
                return os.path.join(tmp_dir, json_files[0])

        raise FileNotFoundError(f"No JSON file found in {tmp_dir}")


def process_metadata_json(file_path: str) -> None:
    file_size = os.path.getsize(file_path) / (1024**3)  # GB
    logger.info(f"檔案大小: {file_size:.2f} GB")  # lambda 極限是 10 GB

    # 讀取資料
    st = time.time()
    df = pd.read_json(file_path, lines=True)
    logger.info(f"讀取資料花費時間: {time.time() - st:.2f} 秒")

    logger.info(f"總記錄數: {df.shape}")

    st = time.time()
    df["update_date_datetime"] = pd.to_datetime(df["update_date"])
    df["update_date_timestamp"] = df["update_date_datetime"].apply(lambda x: x.timestamp())
    df_dedup = df.sort_values("update_date_datetime").drop_duplicates(subset=["id"], keep="last")

    logger.info(f"去重後記錄數: {df_dedup.shape[0]}")
    logger.info(f"去重花費時間: {time.time() - st:.2f} 秒")

    logger.info(json.loads(df_dedup[0:10].to_json(orient="records")))
    # 切分檔案
    # CHUNK_SIZE = 100
    # for i in range(0, len(deduped_data), CHUNK_SIZE):
    #     chunk = deduped_data[i : i + CHUNK_SIZE]
    #     sqs_send_message(chunk)
    #     if i > 10000:
    #         break

    return df_dedup


def sqs_send_message(message: dict) -> None:
    sqs = boto3.client("sqs")
    response = sqs.send_message(
        QueueUrl=os.getenv("SQS_QUEUE_URL"),
        MessageBody=json.dumps(message),
    )
    logger.info(f"Message sent successfully. Message ID: {response['MessageId']}")


if __name__ == "__main__":
    if os.getenv("ENV") == "local":
        lambda_handler(None, None)
