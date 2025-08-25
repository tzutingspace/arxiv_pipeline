from datetime import UTC, datetime


def datetime_to_timestamp(dt: datetime) -> int:
    """
    Convert a datetime object to a Unix timestamp (milliseconds since epoch).

    Args:
        dt: A datetime object, preferably with timezone information.
            If timezone is not provided, UTC is assumed.

    Returns:
        str: Unix timestamp in milliseconds.
    """
    if dt.tzinfo is None:
        # If no timezone is provided, assume UTC
        dt = dt.replace(tzinfo=UTC)

    return int(dt.timestamp() * 1000)


def iso_to_timestamp_ms(iso_string: str) -> int:
    """
    將 ISO 8601 格式的時間字串轉換成毫秒時間戳

    Args:
        iso_string (str): ISO 8601 格式的時間字串，例如 "2025-08-23T23:51:17.850Z"

    Returns:
        int: 毫秒時間戳
    """
    # 解析 ISO 格式時間字串
    dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))

    # 轉換成毫秒時間戳
    timestamp_ms = int(dt.timestamp() * 1000)

    return timestamp_ms


def parse_gmt_time(time_string: str) -> datetime | None:
    """
    解析 GMT 時間字串並轉換為 datetime 物件

    Args:
        time_string (str): GMT 時間格式，例如 "Mon, 2 Apr 2007 19:18:42 GMT"

    Returns:
        datetime: 可比較的 datetime 物件
    """
    try:
        time_without_gmt = time_string.replace(" GMT", "")
        return datetime.strptime(time_without_gmt, "%a, %d %b %Y %H:%M:%S")
    except ValueError as e:
        print(f"解析時間失敗: {time_string}, 錯誤: {e}")
        return None


def extract_latest_version(versions: list[dict[str, str]]):
    latest_date = parse_gmt_time(versions[0]["created"])
    for version in versions[1:]:
        version_date = parse_gmt_time(version["created"])
        if version_date > latest_date:
            latest_date = version_date
    return latest_date
