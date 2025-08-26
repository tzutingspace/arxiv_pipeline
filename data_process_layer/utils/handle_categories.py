def extract_categories(categories_str: str) -> list[dict[str, str]]:
    categories = categories_str.split(" ")
    categories_obj = []
    for category in categories:
        category_obj = {
            "full_category": category,
            "category": category.split(".")[0],
            "subcategory": category.split(".")[1] if len(category.split(".")) > 1 else None,
        }
        categories_obj.append(category_obj)
    return categories_obj
