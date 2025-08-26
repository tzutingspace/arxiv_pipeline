import os

import boto3
from dotenv import load_dotenv
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

load_dotenv()


def main():
    index_name = "arxiv-papers"
    open_search_client = get_open_search_client()
    # Notes: 注意這邊會把原本相同名字的進行刪除
    create_and_init_index(open_search_client, index_name, get_papers_mappings())


def get_open_search_client():
    service = "aoss"
    region = "ap-northeast-1"
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
        service,
        session_token=credentials.token,
    )
    host = os.getenv("OPEN_SEARCH_HOST")
    return OpenSearch(
        hosts=[{"host": host, "port": 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=300,
    )


def create_and_init_index(client: OpenSearch, index_name: str, mappings: dict):
    """創建索引如果不存在"""
    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)
        print(f"已刪除現有索引 '{index_name}'")

    client.indices.create(index=index_name, body=mappings)
    print(f"索引 '{index_name}' 已創建")


def get_papers_mappings() -> dict:
    return {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "submitter": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                },
                "authors": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                },
                "authors_parsed": {"type": "keyword"},
                "authors_full_info": {
                    "type": "nested",
                    "properties": {
                        "fullname": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                        },
                        "keyname": {"type": "keyword"},
                        "firstname": {"type": "keyword"},
                        "lastname": {"type": "keyword"},
                        "affiliation": {"type": "keyword"},
                    },
                },
                "authors_title": {"type": "text"},
                "comments": {"type": "text"},
                "journal-ref": {"type": "text"},
                "doi": {"type": "keyword"},
                "report-no": {"type": "keyword"},
                "categories": {
                    "type": "nested",
                    "properties": {
                        "full_category": {"type": "keyword"},
                        "category": {"type": "keyword"},
                        "subcategory": {"type": "keyword"},
                    },
                },
                "license": {"type": "keyword"},
                "abstract": {"type": "text"},
                "versions": {
                    "type": "nested",
                    "properties": {
                        "version": {"type": "keyword"},
                        "created_str": {"type": "keyword"},
                        "created_timestamp": {"type": "date"},
                    },
                },
                "version_count": {"type": "integer"},
                # 只是為了顯示的時候快速確認日期
                "update_date": {
                    "type": "keyword",
                    "index": False,
                },
                "update_date_datetime": {"type": "date"},
                # "latest_version_date": {"type": "date"},
            }
        }
    }


if __name__ == "__main__":
    main()
