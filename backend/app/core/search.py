def contains_pattern(text: str) -> str:
    """An ILIKE pattern matching `text` anywhere, with % and _ matched literally.

    Use with escape="\\\\". Typed into a search box, % and _ would otherwise be
    wildcards, and "%" alone would match every row.
    """
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"
