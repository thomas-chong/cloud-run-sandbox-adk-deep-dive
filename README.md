# Gemini 3.5 Flash × Google ADK × native Cloud Run sandboxes

A measured, security-focused repository-review agent. Gemini plans and repairs; a native Cloud Run child sandbox executes untrusted repository tests.

![Architecture](assets/architecture.png)

## What is measured

| Evidence | Result |
|---|---:|
| Full multi-tool repair turn | **19,098.54 ms** client wall time |
| Detached sandbox start in that turn | **248.97 ms** |
| Baseline | **1 passed / 3 failed** |
| Generated repair | **2,309 bytes** |
| Verified result | **4 passed / 0 failed** |
| Exported overlay | **5,492,224 bytes** |
| One-shot lifecycle benchmark | **30/30 successful** |
| Lifecycle p50 / p95 / p99 | **428.347 / 455.854 / 470.934 ms** |
| Local quality gates | **14 passed; Ruff clean** |

Raw ADK events are committed under [`assets/evidence/`](assets/evidence/); the graphs are not reconstructed from hand-entered summaries.

![Raw review evidence](assets/full-review-results.png)

## Why a sandbox is necessary

Running `pytest`, `npm test`, build hooks, package scripts, compiler plugins, or generated patches means running repository-controlled code. That code can attempt to:

- read the agent host's environment;
- query the cloud metadata server;
- exfiltrate source or credentials;
- mutate the agent or poison later runs;
- consume CPU, memory, processes, or output indefinitely.

The sample keeps responsibilities separate:

1. **Gemini 3.5 Flash proposes.** It selects typed tools and writes a candidate repair.
2. **Trusted ADK host authorizes.** It fixes sandbox flags and mount paths, validates IDs/source, and bounds time/output.
3. **Cloud Run sandbox contains.** Parent env and metadata are unavailable; egress is denied; writes remain in a disposable overlay or dedicated workspace mount.

Read-only is not confidential: the probe showed that source baked into the service image was readable. Never bake secrets into a sandbox-visible image.

## Version status

Verified July 9, 2026:

- Cloud Run sandboxes: **Public Preview**
- Gemini model: **`gemini-3.5-flash`**, GA, global Vertex AI endpoint
- Python ADK: **`google-adk==2.4.0`**, latest released package
- First-party `CloudRunSandboxCodeExecutor`: landed on ADK `main` after 2.4.0; this repo uses released FunctionTool APIs and a tested lifecycle broker instead of floating on unreleased code

## Repository map

```text
sandbox_analyst/       ADK agent, typed tools, lifecycle, policy, cost model
samples/                intentionally unsafe rule-engine repository
assets/evidence/        raw deployed ADK event JSON
assets/screenshots/     real ADK Web captures
assets/*.png            Google Sans diagrams and measured graphs
docs/tutorial.md        complete technical deep dive
docs/threat-model.md    boundary and residual-risk analysis
docs/decision-matrix.md Cloud Run vs GKE/E2B/Daytona/Modal
scripts/deploy.sh       private Cloud Run deployment with sandbox launcher
scripts/run_evidence.py authenticated evidence harness
scripts/capture_adk_web.py reproducible UI capture through a Cloud Run proxy
```

## Local verification

Local tests mock process creation. They never execute model-generated code on the workstation.

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
```

Verified output:

```text
14 passed, 4 warnings in 0.86s
All checks passed!
```

## Deploy

Prerequisites:

- a Google Cloud project with billing;
- `gcloud` 575.0.1 or newer with the Public Preview sandbox flag;
- permission to enable APIs, create Artifact Registry repositories and service accounts, build images, and deploy Cloud Run;
- Vertex AI access to `gemini-3.5-flash`.

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
./scripts/deploy.sh
```

The service is private, second-generation, scale-to-zero, and deployed with:

```text
2 vCPU · 2 GiB · concurrency 1 · max instances 3 · timeout 3600s
sandbox launcher enabled · session affinity enabled
```

## Save raw evidence

```bash
SERVICE_URL="$(gcloud run services describe sandbox-analyst-adk \
  --region "$REGION" --format='value(status.url)')"

uv run python scripts/run_evidence.py \
  --service-url "$SERVICE_URL" \
  --scenario full-review

uv run python scripts/run_evidence.py \
  --service-url "$SERVICE_URL" \
  --scenario latency
```

## Open ADK Web

```bash
gcloud run services proxy sandbox-analyst-adk \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --port 8080

open http://localhost:8080/dev-ui/
```

Prompt:

```text
Run the full sandboxed security review of the demo repository.
Establish a failing baseline, repair the rule engine, rerun tests,
snapshot the workspace, and always clean up.
```

## Performance evidence

![Raw lifecycle latency](assets/latency-results.png)

The 30-sample benchmark measures only:

```text
inside one warm Cloud Run instance:
sandbox do -- /bin/true = create + execute + delete
```

It excludes Cloud Run cold start, network RTT, Gemini latency, repository setup, and tests.

## Cost model

![Cost breakdown](assets/cost-breakdown.png)

For the documented 10,000-invocation scenario, the estimate is **$157.954**: $7.950 Cloud Run compute, $0.004 requests, $60 Gemini input, and $90 Gemini output. Tokens account for approximately 95% of the estimate.

This excludes free tiers, discounts, builds, registry, logging, storage, and egress. It is not a billing quote.

## Documentation

- [Full tutorial](docs/tutorial.md)
- [Threat model](docs/threat-model.md)
- [Benchmark methodology](docs/benchmark-methodology.md)
- [Cloud Run/GKE/E2B/Daytona/Modal decision matrix](docs/decision-matrix.md)
- [Security policy](SECURITY.md)

## Cleanup

Delete the Cloud Run service after the exercise. Remove the dedicated Artifact Registry repository and service account too if nothing else uses them; scale-to-zero does not remove registry storage charges.

## License

Apache-2.0.
