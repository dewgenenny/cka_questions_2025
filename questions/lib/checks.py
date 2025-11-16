"""Common helper utilities for evaluator scripts."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any, Callable, List, Sequence


@dataclass
class CheckError(Exception):
    """Raised when one or more validation checks fail."""

    message: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message


def run_kubectl_json(
    args: Any, cmd: Sequence[str], namespace: str | None = None
) -> Any:
    """Run ``kubectl`` with ``-o json`` and return the decoded payload."""

    command: List[str] = ["kubectl"]
    kubeconfig = getattr(args, "kubeconfig", None)
    if kubeconfig:
        command.extend(["--kubeconfig", kubeconfig])
    if namespace:
        command.extend(["-n", namespace])
    command.extend(cmd)
    command.extend(["-o", "json"])

    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        raise CheckError(
            f"kubectl command failed (cmd={' '.join(command)}): {stderr or stdout}"
        )
    return json.loads(result.stdout)


def ensure_namespace_exists(args: Any, namespace: str) -> None:
    """Verify that the given namespace is present in the cluster."""

    run_kubectl_json(args, ["get", "namespace", namespace])


def ensure_equal(actual: Any, expected: Any, message: str) -> None:
    """Raise :class:`CheckError` if ``actual`` does not match ``expected``."""

    if actual != expected:
        raise CheckError(f"{message}: expected {expected!r}, got {actual!r}")


class CheckReporter:
    """Utility for printing status information for each check."""

    SUCCESS_ICON = "\033[92m✔\033[0m"
    FAILURE_ICON = "\033[91m✘\033[0m"

    def __init__(self) -> None:
        self._failures: List[str] = []

    def check(self, description: str, func: Callable[[], None]) -> None:
        """Execute ``func`` and record its success or failure."""

        try:
            func()
        except Exception as exc:  # pragma: no cover - relies on kubectl
            self._failures.append(f"{description}: {exc}")
            print(f"{self.FAILURE_ICON} {description}: failed ({exc})")
        else:
            print(f"{self.SUCCESS_ICON} {description}: succeeded")

    def raise_for_failures(self) -> None:
        """Raise :class:`CheckError` if any recorded checks failed."""

        if not self._failures:
            return
        message = "; ".join(self._failures)
        raise CheckError(f"{len(self._failures)} check(s) failed: {message}")

    @property
    def failures(self) -> List[str]:
        """Expose a copy of the recorded failures (useful for testing)."""

        return list(self._failures)
