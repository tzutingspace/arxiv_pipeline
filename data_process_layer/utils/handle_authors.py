def extract_authors(authors_parsed: list[list[str]]) -> list[dict[str, str]]:
    authors_obj = []
    for author in authors_parsed:
        if not isinstance(author, list) or len(author) < 2:
            raise ValueError(f"Each author must be a list with at least 2 elements: {author}")
        author_obj = {
            "fullname": format_author_to_fullname(author),
            "keyname": author[0],
            "firstname": author[1],
            "suffix": author[2] if len(author) > 2 else "",
            "affiliation": author[3:],
        }
        authors_obj.append(author_obj)
    return authors_obj


def format_author_to_fullname(author_data: list[str]) -> str:
    """
    將 [keyname, firstname, suffix, ...] 轉成自然顯示格式
    格式：FirstNames KeyName Suffix

    Args:
        author_data (list[str]): 作者資訊，格式為 [keyname, firstname, suffix, ...]。

    Returns:
        str: 組合後的作者全名字串。
    """
    suffix = author_data[2] if len(author_data) > 2 else ""

    # 組合：FirstNames + KeyName + Suffix
    parts = [author_data[0], author_data[1]]
    if suffix:
        parts.append(suffix)

    return " ".join(filter(None, parts)).strip()
