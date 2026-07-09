# Threat model: untrusted repository verification

## Why the sandbox is necessary

A repository test is arbitrary code. A seemingly routine `pytest`, `npm test`, build
hook, compiler plugin, package installer, or generated patch can:

1. Read parent process credentials and environment variables.
2. Query the cloud metadata server for an access token.
3. Exfiltrate source/data over the network.
4. Modify the agent application or poison subsequent runs.
5. Fork processes, consume memory/CPU, or never terminate.
6. Emit secrets into logs or tool responses.

Prompt instructions and Python AST filters cannot contain these behaviors. The sample
therefore runs repository code only after the native Cloud Run sandbox boundary exists.

## Boundaries exercised by the sample

| Probe | Expected result | Enforced by |
|---|---|---|
| Read `HOST_ONLY_CANARY` | Not visible | Sandbox environment isolation |
| Query metadata service | Blocked/unreachable | Sandbox credential/network isolation |
| Request `https://example.com` | Blocked/unreachable | Egress deny-by-default |
| Write `/sandbox-root-probe` | Succeeds only in the temporary overlay when started with `--write`; host root remains unchanged | Sandbox writable overlay |
| Write `/workspace/workspace-probe.txt` | Succeeds and is visible to the trusted host | Explicit dedicated bind mount |
| Read `/app/sandbox_analyst/agent.py` | **May succeed** | The default rootfs is read-only, not secret |

The last row is the non-obvious caveat: do not bake credentials, private keys, or
sensitive tenant data into the container image. Read-only access prevents mutation;
it does not imply confidentiality. Use a minimal sandbox rootfs when stronger host-file
confidentiality is required.

## Defense in depth, not boundaries

- The agent only receives fixed lifecycle tools, not an unrestricted host shell.
- Sandbox names and paths are validated.
- Tool output is bounded.
- Generated code gets size and syntax checks.
- Execution has a host-side timeout.
- Audit logs store a code hash prefix and outcome, not source or stdout/stderr.

Every item above is bypassable or fallible at the application layer. None replaces
runtime isolation.

## Residual risks

- Sandboxes share the parent Cloud Run instance's allocated CPU and memory. A fork bomb
  or memory bomb can still degrade the host instance; tune concurrency and instance
  limits around the worst allowed task.
- Detached sandbox IDs are local to one service instance. They are not durable session
  handles across Cloud Run rescheduling.
- Bind-mounted workspace files intentionally persist to the host session directory.
  Mount only a per-request directory and validate exported artifacts.
- Sandbox stdout/stderr is untrusted. Never render it as HTML or execute suggested
  commands without escaping and policy checks.
