import json

import boto3


def upload_file_to_s3(bucket_name: str, object_name: str, file_path: str) -> None:
    s3 = boto3.client("s3")
    s3.upload_file(file_path, bucket_name, object_name)


def upload_json_to_s3(data: dict, bucket: str, key: str, **kwargs):
    """上傳 JSON 資料到 S3"""
    s3 = boto3.client("s3")

    default_args = {"ContentType": "application/json", "ServerSideEncryption": "AES256"}
    default_args.update(kwargs)

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(data, ensure_ascii=False),
        **default_args,
    )

    return f"s3://{bucket}/{key}"
