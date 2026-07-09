#!/usr/bin/env python3
"""Exercise an ADK API server endpoint with a reproducible prompt."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.request
import uuid
from pathlib import Path


def token() -> str:
    gcloud = shutil.which("gcloud")
    if not gcloud:
        fallback = Path("/usr/local/share/google-cloud-sdk/bin/gcloud")
        if fallback.is_file():
            gcloud = str(fallback)
        else:
            raise RuntimeError("gcloud CLI not found")
    return subprocess.check_output(
        [gcloud, "auth", "print-identity-token"], text=True
    ).strip()


def request(url: str, method: str, payload: dict | None = None) -> object:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token()}")
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.load(response)


def main() -> int:
    base = os.environ.get("SERVICE_URL", "").rstrip("/")
    if not base:
        print("Set SERVICE_URL to the deployed Cloud Run URL", file=sys.stderr)
        return 2
    user_id = "smoke-user"
    session_id = f"smoke-{uuid.uuid4().hex[:8]}"
    app = "sandbox_analyst"
    request(f"{base}/apps/{app}/users/{user_id}/sessions/{session_id}", "POST", {})
    events = request(
        f"{base}/run",
        "POST",
        {
            "appName": app,
            "userId": user_id,
            "sessionId": session_id,
            "newMessage": {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Run the full sandboxed security review of the demo "
                            "repository. Establish a failing baseline, repair the "
                            "rule engine, rerun tests, snapshot, and clean up."
                        )
                    }
                ],
            },
        },
    )
    print(json.dumps(events, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
