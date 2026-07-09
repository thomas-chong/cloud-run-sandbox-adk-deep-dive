# Benchmark methodology

The benchmark intentionally measures one narrow quantity:

```text
inside one warm Cloud Run instance:
  sandbox do -- /bin/true
  = create + exec(/bin/true) + delete
```

## What the reported distribution includes

- Native child-sandbox creation.
- Process execution of `/bin/true`.
- Sandbox teardown.
- Local CLI/process overhead in the parent container.

## What it excludes

- Cloud Run service cold start.
- Client-to-service network round-trip.
- Gemini 3.5 Flash inference and ADK orchestration.
- Repository checkout, dependency installation, and actual tests.

Combining these stages into one “agent latency” number hides the optimization target.
The evidence harness records client wall time separately from the sandbox lifecycle
distribution.

## Reproduction

Ask the deployed ADK agent:

> Call `benchmark_sandbox_startup` with 30 samples. Report p50, p95, p99,
> mean, minimum, and maximum.

The tool caps a run at 100 samples. Raw successful timings are retained in the returned
JSON, and failures are counted rather than silently discarded.

## Interpreting vendor claims

- Google's Cloud Run launch post reports 1,000 requests that start, execute, and stop
  sandboxes at 500 ms average.
- Google's GKE post reports warm-pool allocation throughput and p90 allocation latency.
- Daytona's “under 90 ms” is a vendor code-to-execution claim.

These are different workloads, percentiles, environments, and control planes. The
article presents them as published reference points, not a ranking.
