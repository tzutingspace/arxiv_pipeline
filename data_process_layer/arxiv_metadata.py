import json
from typing import Any

from utils.handle_authors import extract_authors
from utils.handle_categories import extract_categories
from utils.handle_versions import extract_versions


def lambda_handler(event, context):
    print("START EVENT", event)
    metadata_list = json.loads(event["Records"][0]["body"])
    print(f"來源內容{metadata_list}")
    transformed_records = [transform_record(metadata) for metadata in metadata_list]
    print(f"轉換後內容{transformed_records}")
    return {"status": "success"}


def transform_record(metadata: dict[str, Any]) -> dict[str, Any]:
    """轉換單筆記錄為 OpenSearch 格式"""
    return {
        "id": str(metadata["id"]),
        "submitter": metadata.get("submitter"),
        "title": metadata.get("title"),
        "comments": metadata.get("comments"),
        "journal-ref": metadata.get("journal-ref"),
        "doi": metadata.get("doi"),
        "report-no": metadata.get("report-no"),
        "license": metadata.get("license"),
        "abstract": metadata.get("abstract"),
        "versions": extract_versions(metadata["versions"]),
        "version_count": len(metadata.get("versions", [])),
        "categories": extract_categories(metadata.get("categories")),
        "update_date": metadata.get("update_date"),
        "update_date_datetime": metadata.get("update_date_datetime"),
        "authors": metadata.get("authors"),
        "authors_parsed": metadata.get("authors_parsed"),
        "authors_full_info": extract_authors(metadata.get("authors_parsed")),
    }
