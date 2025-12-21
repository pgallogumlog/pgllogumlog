"""
Shared utility functions.
"""

import re
from typing import Any


def extract_json_from_response(response: str) -> str:
    """
    Extract JSON from a response that may contain markdown code blocks.

    Args:
        response: Raw response text

    Returns:
        Cleaned JSON string
    """
    # Remove markdown code blocks
    cleaned = re.sub(r"^```(?:json)?\s*", "", response, flags=re.MULTILINE)
    cleaned = re.sub(r"```\s*$", "", cleaned, flags=re.MULTILINE)
    return cleaned.strip()


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.

    Args:
        s: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix


def safe_get(d: dict, *keys: str, default: Any = None) -> Any:
    """
    Safely get a nested dictionary value.

    Args:
        d: Dictionary to search
        *keys: Keys to traverse
        default: Default value if not found

    Returns:
        Value at the nested key path, or default
    """
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, default)
        else:
            return default
    return d
