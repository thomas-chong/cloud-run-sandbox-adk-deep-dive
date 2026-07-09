# Security model

## Trust boundaries

- **Trusted:** ADK host process, model credentials, Cloud Run service identity.
- **Untrusted:** user prompts, model-generated Python, sandbox stdout/stderr.
- **Boundary:** the native Cloud Run sandbox runtime, not the Python AST checks.

## Defaults in this sample

- Outbound sandbox network access is disabled.
- Parent environment variables and the metadata server are unavailable to sandboxed code.
- The container root is visible read-only; writes use an ephemeral overlay.
- Each code block runs in a one-shot sandbox with a 20-second host timeout.
- Audit logs retain a truncated SHA-256, outcome, invocation ID, and duration; they omit code and output.

## Non-goals

The AST policy is deliberately small. It reduces accidental invocation of process and
dynamic-evaluation APIs, but Python syntax-level filtering is bypassable. Cloud Run
sandboxing remains mandatory even when all policy checks pass.

Report vulnerabilities privately through GitHub's security advisory flow once the
repository is published.
