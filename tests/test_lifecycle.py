from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sandbox_analyst.lifecycle import SandboxRuntime


def completed() -> MagicMock:
    return MagicMock(returncode=0, stdout="ok\n", stderr="")


def test_start_is_egress_denied_and_mounts_only_session_workspace(
    tmp_path: Path,
) -> None:
    runtime = SandboxRuntime("/sandbox")
    with patch("subprocess.run", return_value=completed()) as run:
        result = runtime.start("review-abc", tmp_path)
    assert result.returncode == 0
    command = run.call_args.args[0]
    assert command[:3] == ["/sandbox", "run", "--write"]
    assert "--allow-egress" not in command
    assert any(str(tmp_path.resolve()) in item for item in command)
    assert command[-3:] == [
        "/bin/sh",
        "-c",
        "while :; do /bin/sleep 3600; done",
    ]


def test_one_shot_egress_requires_explicit_opt_in() -> None:
    runtime = SandboxRuntime("/sandbox")
    with patch("subprocess.run", return_value=completed()) as run:
        runtime.one_shot(["/bin/true"])
    assert "--allow-egress" not in run.call_args.args[0]


def test_invalid_name_is_rejected() -> None:
    with pytest.raises(ValueError, match="sandbox name"):
        SandboxRuntime.validate_name("../../escape")
