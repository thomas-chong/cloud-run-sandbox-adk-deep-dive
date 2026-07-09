"""Thin, testable wrapper around the native Cloud Run ``sandbox`` CLI."""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

SANDBOX_BIN = "/usr/local/gcp/bin/sandbox"
_NAME = re.compile(r"^[a-z][a-z0-9-]{2,47}$")


@dataclass(frozen=True, slots=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class SandboxRuntime:
    """Manage one-shot and detached sandboxes inside one Cloud Run instance."""

    def __init__(self, sandbox_bin: str = SANDBOX_BIN) -> None:
        self.sandbox_bin = sandbox_bin

    @staticmethod
    def validate_name(name: str) -> str:
        if not _NAME.fullmatch(name):
            raise ValueError("sandbox name must match ^[a-z][a-z0-9-]{2,47}$")
        return name

    def start(
        self,
        name: str,
        workspace: Path,
        *,
        allow_egress: bool = False,
        timeout_seconds: int = 30,
    ) -> CommandResult:
        """Start a writable detached sandbox with one dedicated bind mount."""

        name = self.validate_name(name)
        workspace = workspace.resolve(strict=True)
        command = [self.sandbox_bin, "run", "--write"]
        if allow_egress:
            command.append("--allow-egress")
        command.extend(
            [
                "--detach",
                "--mount",
                f"type=bind,source={workspace},destination=/workspace",
                "--workdir",
                "/workspace",
                name,
                "--",
                "/bin/sh",
                "-c",
                "while :; do /bin/sleep 3600; done",
            ]
        )
        return self._run(command, timeout_seconds)

    def exec(
        self,
        name: str,
        command: Sequence[str],
        *,
        timeout_seconds: int = 120,
        workdir: str = "/workspace",
    ) -> CommandResult:
        """Execute an argv-safe command in an existing detached sandbox."""

        name = self.validate_name(name)
        if not command or any(chr(0) in arg for arg in command):
            raise ValueError("command must contain non-NUL argv entries")
        argv = [
            self.sandbox_bin,
            "exec",
            "--workdir",
            workdir,
            name,
            "--",
            *command,
        ]
        return self._run(argv, timeout_seconds)

    def snapshot(
        self,
        name: str,
        destination: Path,
        *,
        timeout_seconds: int = 60,
    ) -> CommandResult:
        """Export the writable overlay of a running sandbox as a tar archive."""

        name = self.validate_name(name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        argv = [
            self.sandbox_bin,
            "tar",
            name,
            f"--file={destination.resolve()}",
        ]
        return self._run(argv, timeout_seconds)

    def delete(
        self, name: str, *, force: bool = True, timeout_seconds: int = 30
    ) -> CommandResult:
        name = self.validate_name(name)
        argv = [self.sandbox_bin, "delete"]
        if force:
            argv.append("--force")
        argv.append(name)
        return self._run(argv, timeout_seconds)

    def one_shot(
        self,
        command: Sequence[str],
        *,
        allow_egress: bool = False,
        timeout_seconds: int = 30,
    ) -> CommandResult:
        argv = [self.sandbox_bin, "do"]
        if allow_egress:
            argv.append("--allow-egress")
        argv.extend(["--", *command])
        return self._run(argv, timeout_seconds)

    @staticmethod
    def python_executable() -> str:
        """Absolute interpreter path visible through the default read-only rootfs."""

        return sys.executable or "/usr/local/bin/python3"

    @staticmethod
    def _run(command: list[str], timeout_seconds: int) -> CommandResult:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return CommandResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
