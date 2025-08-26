import json
import urllib.parse

import boto3
from utils.index_to_db import bulk_index_documents
from utils.transform_metadata import transform_metadata


def lambda_handler(event, context):
    print("START EVENT", event)

    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(event["Records"][0]["s3"]["object"]["key"], encoding="utf-8")
    print("bucket: " + bucket)
    print("key: " + key)

    try:
        s3 = boto3.client("s3")
        response = s3.get_object(Bucket=bucket, Key=key)
        metadata_list = json.loads(response["Body"].read().decode("utf-8"))
    except Exception as e:
        print(e)
        print(
            f"Error getting object {key} from bucket {bucket}. Make sure they exist and your bucket is in the same region as this function."
        )
        raise e

    # print(f"來源內容{metadata_list}")

    transformed_records = [transform_metadata(metadata) for metadata in metadata_list]
    # print(f"轉換後內容{transformed_records}")

    success, failed = bulk_index_documents("arxiv-papers", transformed_records)
    print(f"成功索引 {success} 條記錄，失敗 {failed} 條記錄")
    return {"status": "success"}


##### 地端測試用
def mock_event():
    return {
        "Records": [
            {
                "eventVersion": "2.0",
                "eventSource": "aws:s3",
                "awsRegion": "us-east-1",
                "eventTime": "1970-01-01T00:00:00.000Z",
                "eventName": "ObjectCreated:Put",
                "userIdentity": {"principalId": "EXAMPLE"},
                "requestParameters": {"sourceIPAddress": "127.0.0.1"},
                "responseElements": {
                    "x-amz-request-id": "EXAMPLE123456789",
                    "x-amz-id-2": "EXAMPLE123/5678abcdefghijklambdaisawesome/mnopqrstuvwxyzABCDEFGH",
                },
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "testConfigRule",
                    "bucket": {
                        "name": "arxiv-dateset",
                        "ownerIdentity": {"principalId": "EXAMPLE"},
                        "arn": "arn:aws:s3:::arxiv-dateset",
                    },
                    "object": {
                        "key": "parsed_1755993077850/metadata-1000.json",
                        "size": 1024,
                        "eTag": "0123456789abcdef0123456789abcdef",
                        "sequencer": "0A1B2C3D4E5F678901",
                    },
                },
            }
        ]
    }


if __name__ == "__main__":
    lambda_handler(mock_event(), None)
