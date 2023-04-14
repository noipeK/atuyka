"""Text manipulation utilities."""
import re

__all__ = ["to_snake_case"]


def to_snake_case(text: str) -> str:
    """Convert text to snake case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", text).lower()
