# Sandbox decision matrix

Checked against vendor documentation on **2026-07-09**. Product claims are not
cross-vendor benchmark results. Isolation units, workload shapes, and billing meters
differ, so headline latency and unit prices are not directly comparable.

| Dimension | Cloud Run sandboxes | GKE Agent Sandbox | E2B | Daytona | Modal Sandboxes |
|---|---|---|---|---|---|
| Control plane | Built into each Cloud Run service instance | Kubernetes CRDs/controller/router on GKE | Hosted sandbox API/SDK | Hosted API/SDK/CLI | Hosted Modal API/SDK |
| Execution scope | Child sandbox shares the host instance's allocated CPU/memory | Dedicated sandbox Pod scheduled to cluster nodes; warm pools optional | Isolated sandbox; default 2 vCPU/512 MiB | Container or VM sandbox with dedicated resources | Secure runtime container with explicit requests/limits |
| Network default | **No outbound egress** unless `--allow-egress` | Public egress allowed; private ranges, cluster DNS, and metadata blocked under managed policy | Configurable hosted networking | Dedicated network stack; lifecycle/network options vary by class | Tunnels, volumes, secrets, and networking configured through Modal |
| Host credentials | Parent env and metadata server unavailable | Service-account token disabled in recommended template; metadata blocked by managed policy | Vendor API separates caller and sandbox | Vendor API separates caller and sandbox | Secrets may be explicitly injected |
| Persistence | Ephemeral overlay; tar import/export, bind mounts, `--sync-tar`; state is instance-local unless exported to durable storage | Pod Snapshots and Kubernetes storage patterns | Pause/resume can preserve filesystem + memory; snapshots | Stop/archive/snapshot; VM pause/fork supports memory state | Filesystem Snapshots and Volumes; sandbox lifetime up to 24 hours |
| Long-running fit | One Cloud Run request/instance; service request timeout and instance rescheduling bound the lifecycle | Strong fit for cluster-native, high-scale, multi-Pod workflows | Hosted persistent sessions; 1h Hobby / 24h Pro continuous runtime | Stateful containers/VMs with auto-stop/archive/delete controls | Detached sandboxes, readiness probes, up to 24h then snapshot/restore |
| Published latency claim | Google launch demo: 1,000 start/execute/stop requests averaged **500 ms** | Warm pool: 300 allocations/s/cluster; 90% in **200 ms** | Do not compare without measuring the same workload | Vendor says **under 90 ms** code-to-execution | No same-shape number used in this tutorial |
| Sandbox premium | None; normal Cloud Run CPU/memory/request charges | None; GKE resource/cluster charges apply | Per-second CPU/RAM plus plan limits; Pro is $150/mo + usage | Usage-based CPU/RAM/disk; public page did not expose stable unit rates in extracted docs | Per-second max(request, actual) CPU/memory; plan/credits also apply |
| Operational ownership | Lowest if the agent already runs on Cloud Run | Highest flexibility and Kubernetes operations | Vendor-managed | Vendor-managed | Vendor-managed |
| Choose it when | Google Cloud-native, bursty request-bound agents; zero-egress default; minimal control plane | Custom images/policies, large warm pools, cross-request state, cluster integration | You need hosted durable sessions and a sandbox-centric SDK | You need persistent composable containers/VMs and rich lifecycle controls | You want serverless sandbox compute, volumes, tunnels, GPUs, and long-lived services |

## Cost-rate snapshot

These are published list rates, not a normalized TCO comparison:

- **Cloud Run request-based tier-1 active time:** $0.000024/vCPU-second,
  $0.0000025/GiB-second, plus $0.40/million requests. Sandboxes have no separate
  premium and share the service instance allocation.
- **E2B:** $0.000014/vCPU-second and $0.0000045/GiB-second; Pro is $150/month
  plus usage. Storage and plan limits differ.
- **Modal:** $0.0000131/physical-core-second (two-vCPU equivalent) and
  $0.00000222/GiB-second, billed by `max(request, actual)`.
- **GKE:** no Agent Sandbox fee; node, cluster, storage, and networking costs apply.
- **Daytona:** usage-based billing by CPU-seconds, RAM GB-seconds, and disk
  GB-seconds; use its current calculator for rates.

## Sources

- [Cloud Run sandbox launch post](https://cloud.google.com/blog/topics/developers-practitioners/google-cloud-run-sandboxes-are-in-public-preview/)
- [Cloud Run code execution](https://docs.cloud.google.com/run/docs/code-execution)
- [Cloud Run pricing](https://cloud.google.com/run/pricing)
- [GKE Agent Sandbox guide](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/agent-sandbox)
- [GKE Agent Sandbox launch](https://cloud.google.com/blog/products/containers-kubernetes/bringing-you-agent-sandbox-on-gke-and-agent-substrate)
- [E2B billing](https://e2b.dev/docs/billing), [pricing](https://e2b.dev/pricing), and [persistence](https://e2b.dev/docs/sandbox/persistence)
- [Daytona docs](https://www.daytona.io/docs/en.md), [sandboxes](https://www.daytona.io/docs/en/sandboxes/), and [billing](https://www.daytona.io/docs/en/billing.md)
- [Modal Sandboxes](https://modal.com/docs/guide/sandboxes), [resources](https://modal.com/docs/guide/sandbox-resources), and [pricing](https://modal.com/pricing)
