"""ADK function tools for a stateful repository-verification workflow."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import statistics
import time
import uuid
from pathlib import Path

from .costs import estimate_cost
from .lifecycle import SandboxRuntime
from .policy import ExecutionPolicy, evaluate_python

logger = logging.getLogger(__name__)
RUNTIME = SandboxRuntime()
SESSION_ROOT = Path(os.getenv("SANDBOX_SESSION_ROOT", "/tmp/sandbox-review-sessions"))
SAMPLE_REPO = Path(__file__).resolve().parents[1] / "samples" / "unsafe_rule_engine"
MAX_BENCHMARK_SAMPLES = 100


def _workspace(sandbox_id: str) -> Path:
    RUNTIME.validate_name(sandbox_id)
    path = SESSION_ROOT / sandbox_id / "workspace"
    if not path.is_dir():
        raise ValueError(f"unknown workspace: {sandbox_id}")
    return path


def start_review_workspace() -> dict[str, object]:
    """Start a detached, egress-denied sandbox containing an unsafe demo repo.

    Returns a workspace ID and launch latency. The workspace is valid only inside
    the current Cloud Run instance and must be deleted with finish_review_workspace.
    """

    sandbox_id = f"review-{uuid.uuid4().hex[:12]}"
    workspace = SESSION_ROOT / sandbox_id / "workspace"
    workspace.parent.mkdir(parents=True, exist_ok=False)
    shutil.copytree(SAMPLE_REPO, workspace)
    started = time.perf_counter()
    result = RUNTIME.start(sandbox_id, workspace, allow_egress=False)
    launch_ms = round((time.perf_counter() - started) * 1000, 2)
    if result.returncode != 0:
        shutil.rmtree(workspace.parent, ignore_errors=True)
        return {
            "status": "error",
            "phase": "sandbox_start",
            "launch_ms": launch_ms,
            "stderr": result.stderr,
        }
    return {
        "status": "running",
        "workspace_id": sandbox_id,
        "launch_ms": launch_ms,
        "egress": "denied",
        "lifecycle_scope": "current Cloud Run instance",
    }


def inspect_security_boundaries(workspace_id: str) -> dict[str, object]:
    """Run harmless probes for env, metadata, egress, rootfs, and mount boundaries."""

    _workspace(workspace_id)
    result = RUNTIME.exec(
        workspace_id,
        [RUNTIME.python_executable(), "/workspace/security_probe.py"],
        timeout_seconds=20,
    )
    payload: object = None
    if result.stdout:
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = {"unparsed_stdout": result.stdout}
    return {
        "status": "success" if result.returncode == 0 else "error",
        "returncode": result.returncode,
        "probe": payload,
        "stderr": result.stderr,
    }


def run_test_suite(workspace_id: str) -> dict[str, object]:
    """Execute the untrusted repository's tests inside the existing sandbox."""

    _workspace(workspace_id)
    started = time.perf_counter()
    result = RUNTIME.exec(
        workspace_id,
        [
            RUNTIME.python_executable(),
            "-m",
            "pytest",
            "-q",
            "--disable-warnings",
            "/workspace/tests",
        ],
        timeout_seconds=120,
    )
    return {
        "status": "passed" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        "stdout": result.stdout[-8_000:],
        "stderr": result.stderr[-4_000:],
    }


def write_candidate_rule_engine(
    workspace_id: str, source_code: str
) -> dict[str, object]:
    """Write a model-proposed rule_engine.py without executing it in the host.

    The destination path is fixed. Syntax/size checks are quality gates, not a
    security boundary; subsequent imports and tests still run only in the sandbox.
    """

    workspace = _workspace(workspace_id)
    decision = evaluate_python(
        source_code,
        ExecutionPolicy(
            max_code_bytes=24_576,
            blocked_modules=frozenset(),
            blocked_calls=frozenset(),
        ),
    )
    if not decision.allowed:
        return {"status": "rejected", "reason": decision.reason}
    destination = workspace / "rule_engine.py"
    destination.write_text(source_code, encoding="utf-8")
    digest = hashlib.sha256(source_code.encode()).hexdigest()
    return {
        "status": "written",
        "path": "rule_engine.py",
        "sha256": digest,
        "bytes": len(source_code.encode()),
    }


def snapshot_workspace(workspace_id: str) -> dict[str, object]:
    """Export the sandbox's writable overlay before deletion.

    Bind-mounted workspace files already live in the dedicated host session path;
    the tar captures other overlay changes. It remains instance-local in this demo.
    """

    workspace = _workspace(workspace_id)
    destination = workspace.parent / "overlay.tar"
    result = RUNTIME.snapshot(workspace_id, destination)
    return {
        "status": "created" if result.returncode == 0 else "error",
        "path": str(destination),
        "bytes": destination.stat().st_size if destination.exists() else 0,
        "stderr": result.stderr,
    }


def finish_review_workspace(workspace_id: str) -> dict[str, object]:
    """Force-delete the sandbox and remove its dedicated host-side workspace."""

    workspace = _workspace(workspace_id)
    result = RUNTIME.delete(workspace_id, force=True)
    shutil.rmtree(workspace.parent, ignore_errors=True)
    return {
        "status": "deleted" if result.returncode == 0 else "error",
        "returncode": result.returncode,
        "stderr": result.stderr,
    }


def benchmark_sandbox_startup(samples: int = 20) -> dict[str, object]:
    """Measure warm-instance one-shot create/exec/delete latency.

    This does not include Cloud Run service cold start or Gemini latency. Samples
    are capped to control cost and prevent one model call from monopolizing an
    instance.
    """

    if not 1 <= samples <= MAX_BENCHMARK_SAMPLES:
        raise ValueError(f"samples must be between 1 and {MAX_BENCHMARK_SAMPLES}")
    timings: list[float] = []
    failures: list[str] = []
    for _ in range(samples):
        started = time.perf_counter()
        result = RUNTIME.one_shot(["/bin/true"], timeout_seconds=10)
        elapsed = round((time.perf_counter() - started) * 1000, 3)
        if result.returncode == 0:
            timings.append(elapsed)
        else:
            failures.append(result.stderr[-500:])
    if not timings:
        return {"status": "error", "samples": 0, "failures": failures}
    ordered = sorted(timings)

    def percentile(p: float) -> float:
        index = max(0, min(len(ordered) - 1, round(p * (len(ordered) - 1))))
        return ordered[index]

    summary = {
        "status": "success" if not failures else "partial",
        "metric": "sandbox do -- /bin/true wall time",
        "scope": "inside one warm Cloud Run service instance",
        "successful_samples": len(timings),
        "failed_samples": len(failures),
        "min_ms": ordered[0],
        "p50_ms": round(statistics.median(ordered), 3),
        "p95_ms": percentile(0.95),
        "p99_ms": percentile(0.99),
        "max_ms": ordered[-1],
        "mean_ms": round(statistics.fmean(ordered), 3),
        "raw_ms": ordered,
        "excludes": ["Cloud Run cold start", "network RTT", "Gemini latency"],
    }
    logger.info(json.dumps({"event": "sandbox_benchmark", **summary}))
    return summary


def estimate_monthly_cost(
    invocations: int,
    active_seconds_per_invocation: float,
    effective_concurrency: float,
    input_tokens_per_invocation: int,
    output_tokens_per_invocation: int,
) -> dict[str, object]:
    """Estimate monthly list-price cost for the sample's 2-vCPU, 2-GiB service."""

    return estimate_cost(
        invocations=invocations,
        active_seconds_per_invocation=active_seconds_per_invocation,
        vcpu=2,
        memory_gib=2,
        effective_concurrency=effective_concurrency,
        input_tokens_per_invocation=input_tokens_per_invocation,
        output_tokens_per_invocation=output_tokens_per_invocation,
    ).as_dict()
