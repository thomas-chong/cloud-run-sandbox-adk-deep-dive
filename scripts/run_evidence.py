#!/usr/bin/env python3
"""Run reproducible ADK scenarios and save raw events for the tutorial."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.request
import uuid
from pathlib import Path

SCENARIOS = {
    "full-review": (
        "Run the full sandboxed security review of the demo repository. "
        "Establish a failing baseline, repair the rule engine, rerun tests, "
        "snapshot the workspace, and always clean up."
    ),
    "latency": (
        "Call benchmark_sandbox_startup with 30 samples. Report the observed "
        "p50, p95, p99, mean, minimum, and maximum, and explicitly distinguish "
        "this warm-instance metric from Cloud Run cold start and model latency."
    ),
    "cost": (
        "Estimate monthly cost for 1,000 repository reviews, 30 active sandbox "
        "seconds per review, effective concurrency 2, 3,000 Gemini input tokens, "
        "and 500 output tokens. Explain which component dominates and list every "
        "excluded cost."
    ),
}


def identity_token() -> str:
    return subprocess.check_output(
        [
            "/usr/local/share/google-cloud-sdk/bin/gcloud",
            "auth",
            "print-identity-token",
        ],
        text=True,
    ).strip()


def request(
    base_url: str,
    path: str,
    method: str,
    token: str,
    payload: dict[str, object] | None = None,
) -> object:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"{base_url}{path}", data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=3_900) as response:
        return json.load(response)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--service-url", required=True)
    parser.add_argument("--scenario", choices=[*SCENARIOS, "all"], default="all")
    parser.add_argument("--output", type=Path, default=Path("assets/evidence"))
    args = parser.parse_args()
    base_url = args.service_url.rstrip("/")
    args.output.mkdir(parents=True, exist_ok=True)
    token = identity_token()
    names = list(SCENARIOS) if args.scenario == "all" else [args.scenario]

    for name in names:
        session_id = f"evidence-{name}-{uuid.uuid4().hex[:8]}"
        request(
            base_url,
            f"/apps/sandbox_analyst/users/tutorial/sessions/{session_id}",
            "POST",
            token,
            {},
        )
        started = time.perf_counter()
        events = request(
            base_url,
            "/run",
            "POST",
            token,
            {
                "appName": "sandbox_analyst",
                "userId": "tutorial",
                "sessionId": session_id,
                "newMessage": {
                    "role": "user",
                    "parts": [{"text": SCENARIOS[name]}],
                },
            },
        )
        record = {
            "scenario": name,
            "service_url": base_url,
            "session_id": session_id,
            "client_wall_ms": round((time.perf_counter() - started) * 1_000, 2),
            "events": events,
        }
        destination = args.output / f"{name}.json"
        destination.write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(f"{name}: {destination} ({record['client_wall_ms']} ms)")


if __name__ == "__main__":
    main()
