"""Audited ADK code executor for the native Cloud Run ``sandbox`` CLI.

ADK 2.4.0 is the latest released package on 2026-07-09. Google's first-party
``CloudRunSandboxCodeExecutor`` landed on ADK main after that release. This small
adapter uses only ADK's stable ``BaseCodeExecutor`` interface and can be removed
when the next release contains the upstream integration.
"""

from __future__ import annotations

import hashlib
import json
import logging
import subprocess
import sys
import time

from google.adk.agents.invocation_context import InvocationContext
from google.adk.code_executors.base_code_executor import BaseCodeExecutor
from google.adk.code_executors.code_execution_utils import (
    CodeExecutionInput,
    CodeExecutionResult,
)
from pydantic import Field
from typing_extensions import override

from .policy import ExecutionPolicy, evaluate_python

logger = logging.getLogger(__name__)
_POLICY = ExecutionPolicy()


class AuditedCloudRunSandboxCodeExecutor(BaseCodeExecutor):
    """Execute generated Python in one-shot, egress-denied Cloud Run sandboxes."""

    sandbox_bin: str = "/usr/local/gcp/bin/sandbox"
    allow_egress: bool = False
    stateful: bool = Field(default=False, frozen=True, exclude=True)
    optimize_data_file: bool = Field(default=False, frozen=True, exclude=True)

    def __init__(self, **data: object) -> None:
        if data.get("stateful"):
            raise ValueError("Cloud Run one-shot code execution cannot be stateful")
        if data.get("optimize_data_file"):
            raise ValueError("Cloud Run one-shot executor does not inject data files")
        super().__init__(**data)

    @override
    def execute_code(
        self,
        invocation_context: InvocationContext,
        code_execution_input: CodeExecutionInput,
    ) -> CodeExecutionResult:
        code = code_execution_input.code
        digest = hashlib.sha256(code.encode("utf-8")).hexdigest()[:16]
        decision = evaluate_python(code, _POLICY)
        if not decision.allowed:
            self._audit(
                invocation_context.invocation_id,
                digest,
                "policy_blocked",
                0,
                decision.reason,
            )
            return CodeExecutionResult(
                stdout="",
                stderr=f"POLICY_BLOCKED: {decision.reason}",
                output_files=[],
            )

        command = [self.sandbox_bin, "do"]
        if self.allow_egress:
            command.append("--allow-egress")
        command.extend(["--", sys.executable or "/usr/local/bin/python3", "-I", "-B"])
        started = time.perf_counter()

        try:
            completed = subprocess.run(
                command,
                input=code,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            elapsed_ms = round((time.perf_counter() - started) * 1000)
            stderr = _as_text(exc.stderr) or (
                f"Code execution timed out after {self.timeout_seconds} seconds."
            )
            self._audit(
                invocation_context.invocation_id,
                digest,
                "timeout",
                elapsed_ms,
                "host_timeout",
            )
            return CodeExecutionResult(
                stdout=_as_text(exc.stdout),
                stderr=stderr,
                output_files=[],
            )
        except OSError as exc:
            elapsed_ms = round((time.perf_counter() - started) * 1000)
            self._audit(
                invocation_context.invocation_id,
                digest,
                "launcher_error",
                elapsed_ms,
                type(exc).__name__,
            )
            return CodeExecutionResult(
                stdout="",
                stderr=f"Unable to launch Cloud Run sandbox: {exc}",
                output_files=[],
            )

        elapsed_ms = round((time.perf_counter() - started) * 1000)
        self._audit(
            invocation_context.invocation_id,
            digest,
            "success" if completed.returncode == 0 else "sandbox_error",
            elapsed_ms,
            f"returncode_{completed.returncode}",
        )
        return CodeExecutionResult(
            stdout=completed.stdout,
            stderr=completed.stderr,
            output_files=[],
        )

    @staticmethod
    def _audit(
        invocation_id: str,
        digest: str,
        outcome: str,
        elapsed_ms: int,
        detail: str,
    ) -> None:
        record = {
            "event": "sandbox_execution",
            "invocation_id": invocation_id,
            "code_sha256_prefix": digest,
            "outcome": outcome,
            "elapsed_ms": elapsed_ms,
            "detail": detail,
        }
        logger.info(json.dumps(record, separators=(",", ":"), sort_keys=True))


def _as_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
