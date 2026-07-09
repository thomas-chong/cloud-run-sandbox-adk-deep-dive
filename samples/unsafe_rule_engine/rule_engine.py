"""Deliberately unsafe baseline for the tutorial's repair workflow."""


class UnsafeExpression(ValueError):
    """Raised when a rule contains unsupported syntax."""


def evaluate_rule(expression: str, record: dict[str, object]) -> bool:
    """Evaluate a business rule against one record.

    WARNING: ``eval`` is intentional here so the sandboxed agent has a real defect
    to diagnose and repair. Never copy this implementation into production.
    """

    return bool(eval(expression, {"__builtins__": {}}, record))  # noqa: S307
