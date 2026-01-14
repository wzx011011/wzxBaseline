"""
Common utilities for filament parameter validation.
"""

from typing import Any


def str_norm(v: Any) -> str | None:
    """Normalize value for comparison. Treats None and 'nil' as equivalent."""
    if v is None:
        return None
    s = str(v).strip()
    # Treat 'nil' as None for comparison
    if s.lower() == 'nil':
        return None
    return s


def values_equal(actual: Any, expected: Any) -> bool:
    """Compare values, treating None and 'nil' as equivalent."""
    norm_actual = str_norm(actual)
    norm_expected = str_norm(expected)
    return norm_actual == norm_expected

