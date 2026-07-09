from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from google.adk.code_executors.code_execution_utils import CodeExecutionInput

from sandbox_analyst.executor import AuditedCloudRunSandboxCodeExecutor


def context() -> SimpleNamespace:
    return SimpleNamespace(invocation_id="inv-test")


def test_policy_block_short_circuits_subprocess() -> None:
    executor = AuditedCloudRunSandboxCodeExecutor()
    with patch("subprocess.run") as run:
        result = executor.execute_code(
            context(), CodeExecutionInput(code="import subprocess")
        )
    run.assert_not_called()
    assert result.stderr == "POLICY_BLOCKED: blocked import: subprocess"


def test_allowed_code_uses_cloud_run_sandbox_binary() -> None:
    executor = AuditedCloudRunSandboxCodeExecutor(timeout_seconds=7)
    completed = MagicMock(returncode=0, stdout="3\n", stderr="")
    with patch("subprocess.run", return_value=completed) as run:
        result = executor.execute_code(
            context(), CodeExecutionInput(code="print(1 + 2)")
        )
    assert result.stdout == "3\n"
    command = run.call_args.args[0]
    assert command[:2] == ["/usr/local/gcp/bin/sandbox", "do"]
    assert "--allow-egress" not in command
    assert command[-2:] == ["-I", "-B"]
    assert run.call_args.kwargs["timeout"] == 7


def test_egress_is_opt_in_not_default() -> None:
    executor = AuditedCloudRunSandboxCodeExecutor(allow_egress=True)
    completed = MagicMock(returncode=0, stdout="ok\n", stderr="")
    with patch("subprocess.run", return_value=completed) as run:
        executor.execute_code(context(), CodeExecutionInput(code="print('ok')"))
    assert "--allow-egress" in run.call_args.args[0]
