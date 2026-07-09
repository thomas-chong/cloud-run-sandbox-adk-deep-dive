"""Harmless boundary probes. The output is evidence, not an exploit."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path


def try_url(url: str) -> dict[str, object]:
    try:
        with urllib.request.urlopen(url, timeout=1) as response:
            return {"reachable": True, "status": response.status}
    except Exception as exc:  # Exact exception varies by runtime policy.
        return {"reachable": False, "error_type": type(exc).__name__}


def try_write(path: Path) -> dict[str, object]:
    try:
        path.write_text("probe", encoding="utf-8")
        return {"writable": True}
    except Exception as exc:
        return {"writable": False, "error_type": type(exc).__name__}


result = {
    "parent_canary_visible": os.getenv("HOST_ONLY_CANARY") is not None,
    "metadata_server": try_url(
        "http://metadata.google.internal/computeMetadata/v1/instance/id"
    ),
    "public_egress": try_url("https://example.com"),
    "root_filesystem": try_write(Path("/sandbox-root-probe")),
    "workspace_mount": try_write(Path("/workspace/workspace-probe.txt")),
    "host_application_source_visible": Path(
        "/app/sandbox_analyst/agent.py"
    ).exists(),
}
print(json.dumps(result, sort_keys=True))
