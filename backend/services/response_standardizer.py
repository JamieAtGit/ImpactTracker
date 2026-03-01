from typing import Any, Dict


_MISSING_TOKENS = {"", "unknown", "none", "n/a", "na", "null"}


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in _MISSING_TOKENS
    if isinstance(value, (list, tuple, dict)):
        return len(value) == 0
    return False


def standardize_attributes(attributes: Dict[str, Any], fields: list[str]) -> Dict[str, Any]:
    normalized = dict(attributes)
    for field in fields:
        if _is_missing(normalized.get(field)):
            normalized[field] = "Not found"
    return normalized
