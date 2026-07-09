#!/usr/bin/env python3
"""CLI wrapper for the transparent tutorial cost model."""

from __future__ import annotations

import argparse
import json

from sandbox_analyst.costs import estimate_cost


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--invocations", type=int, required=True)
    parser.add_argument("--seconds", type=float, required=True)
    parser.add_argument("--vcpu", type=float, default=2)
    parser.add_argument("--memory-gib", type=float, default=2)
    parser.add_argument("--concurrency", type=float, default=1)
    parser.add_argument("--input-tokens", type=int, default=2_000)
    parser.add_argument("--output-tokens", type=int, default=500)
    args = parser.parse_args()
    result = estimate_cost(
        invocations=args.invocations,
        active_seconds_per_invocation=args.seconds,
        vcpu=args.vcpu,
        memory_gib=args.memory_gib,
        effective_concurrency=args.concurrency,
        input_tokens_per_invocation=args.input_tokens,
        output_tokens_per_invocation=args.output_tokens,
    )
    print(json.dumps(result.as_dict(), indent=2))


if __name__ == "__main__":
    main()
