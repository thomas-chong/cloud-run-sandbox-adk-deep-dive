"""Application-level policy checks for model-generated Python.

These checks reduce accidental misuse and create a reviewable policy surface. They are
not a security boundary; Cloud Run sandbox isolation is the security boundary.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ExecutionPolicy:
    """Small, explicit policy applied before a sandbox process is created."""

    max_code_bytes: int = 16_384
    blocked_modules: frozenset[str] = field(
        default_factory=lambda: frozenset({"ctypes", "multiprocessing", "subprocess"})
    )
    blocked_calls: frozenset[str] = field(
        default_factory=lambda: frozenset({"compile", "eval", "exec", "__import__"})
    )


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    reason: str


def evaluate_python(code: str, policy: ExecutionPolicy) -> PolicyDecision:
    """Return a deterministic decision without executing *code*."""

    size = len(code.encode("utf-8"))
    if size > policy.max_code_bytes:
        return PolicyDecision(
            False,
            f"code is {size} bytes; limit is {policy.max_code_bytes}",
        )

    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as exc:
        return PolicyDecision(False, f"syntax error at line {exc.lineno}: {exc.msg}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name.split(".", 1)[0] for alias in node.names]
            blocked = sorted(set(names) & policy.blocked_modules)
            if blocked:
                return PolicyDecision(False, f"blocked import: {', '.join(blocked)}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            top_level = node.module.split(".", 1)[0]
            if top_level in policy.blocked_modules:
                return PolicyDecision(False, f"blocked import: {top_level}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in policy.blocked_calls:
                return PolicyDecision(False, f"blocked call: {node.func.id}")

    return PolicyDecision(True, "allowed")
