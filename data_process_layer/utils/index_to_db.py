import os

import boto3
from dotenv import load_dotenv
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.helpers import bulk
from requests_aws4auth import AWS4Auth

load_dotenv()


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


def bulk_index_documents(index_name: str, documents: list[dict]):
    client = get_open_search_client()

    actions = [{"_index": index_name, "_id": doc["id"], "_source": doc} for doc in documents]

    success, failed = bulk(client, actions)

    return success, failed
