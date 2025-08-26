import logging
from datetime import datetime


def parse_gmt_time(gmt_time_string: str) -> int:
    try:
        time_without_gmt = gmt_time_string.replace(" GMT", "")
        return int(datetime.strptime(time_without_gmt, "%a, %d %b %Y %H:%M:%S").timestamp())
    except ValueError as e:
        logging.error(f"解析時間失敗: {gmt_time_string}, 錯誤: {e}")
        raise e


def extract_versions(versions: list[dict[str, str]]) -> list[dict[str, str | int]]:
    outputs = []

    for version in versions:
        created_time = parse_gmt_time(version["created"])
        if created_time:
            outputs.append(
                {
                    "version": version["version"],
                    "created_str": version["created"],
                    "created_timestamp": created_time,
                },
            )

    return outputs
