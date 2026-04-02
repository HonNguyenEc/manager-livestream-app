"""Shared helper utilities used across modules."""


def to_num(v: str):
    """Convert numeric string to int, otherwise return original value."""
    return int(v) if str(v).isdigit() else v


def to_bool(v: str) -> bool:
    """Convert common truthy string representations to bool."""
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}
