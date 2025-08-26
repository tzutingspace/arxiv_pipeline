import gc
import json
import logging
import os
import time
from datetime import datetime

import boto3
from dotenv import load_dotenv
from utils.format_time import iso_to_timestamp_ms
from utils.s3 import upload_file_to_s3, upload_json_to_s3

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
    process_metadata(source_file_path, latest_update_timestamp)

    # 6. 上傳最新的 metadata.json 至 S3, 表示已進入下一個流程
    new_file_name = f"{S3_FOLDER_PREFIX}-{latest_update_timestamp}.json"
    upload_file_to_s3(S3_BUCKET_NAME, new_file_name, source_file_path)

    return {"status": "success"}


def get_latest_processed_timestamp() -> int:
    s3 = boto3.client("s3")
    response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=S3_FOLDER_PREFIX)
    if "Contents" not in response:
        return 0
    latest_file = max(response["Contents"], key=lambda x: x["LastModified"])
    logger.info(f"latest_processed_file: {latest_file}")
    return latest_file["Key"].split("-")[-1].split(".")[0]


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


def process_metadata(file_path: str, timestamp_str: str):
    processed_count = 0
    error_count = 0

    id_update_map = {}
    results = []
    with open(file_path, encoding="utf-8") as file:
        for line_num, line in enumerate(file, 1):
            line = line.strip()

            # 跳過空行
            if not line:
                continue

            try:
                item = json.loads(line)
                result = process_single_item(item)

                if result["id"] not in id_update_map:
                    id_update_map[result["id"]] = result["update_timestamp"]

                # 該筆資料較舊，跳過
                elif result["update_timestamp"] < id_update_map[result["id"]]:
                    continue

                processed_count += 1
                results.append(result)

                # 定期清理記憶體
                if processed_count % 1000 == 0:
                    logger.info(f"已處理 {processed_count} 筆")
                    upload_json_to_s3(
                        results,
                        S3_BUCKET_NAME,
                        f"parsed_{timestamp_str}/metadata-{processed_count}.json",
                    )
                    results.clear()
                    gc.collect()

                # TODO: 因為測試而已，限定數量
                if processed_count >= 100000:
                    break

            except json.JSONDecodeError as e:
                error_count += 1
                if error_count <= 10:  # 只印前 10 個錯誤
                    logger.error(f"第 {line_num} 行 JSON 錯誤: {e}")
                    logger.error(f"問題行: {line[:100]}...")
                continue

            except Exception as e:
                error_count += 1
                logger.error(f"第 {line_num} 行處理錯誤: {e}")
                continue

    logger.info(f"處理完成: 成功 {processed_count} 筆, 錯誤 {error_count} 筆")
    return processed_count


def process_single_item(item):
    update_time_str = item["update_date"]
    dt = datetime.strptime(update_time_str, "%Y-%m-%d")
    item["update_timestamp"] = int(dt.timestamp())
    return item


if __name__ == "__main__":
    if os.getenv("ENV") == "local":
        lambda_handler(None, None)
