#!/usr/bin/env python3
"""Validation script for the "Web App Ingress Routing" question."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Callable, List, Sequence

NAMESPACE = "ingress-ns"
INGRESS_NAME = "webapp-ingress"
EXPECTED_HOST = "webapp.practice.local"
EXPECTED_SERVICE = "webapp-svc"
EXPECTED_PATH = "/"
EXPECTED_PATHTYPE = "Prefix"
EXPECTED_SERVICE_PORT = 80


@dataclass
class CheckError(Exception):
    message: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the webapp ingress configuration")
    parser.add_argument(
        "--kubeconfig",
        default=None,
        help="Path to the kubeconfig file (defaults to $KUBECONFIG or ~/.kube/config)",
    )
    return parser.parse_args(argv)


def run_kubectl_json(
    args: argparse.Namespace, cmd: Sequence[str], namespace: str | None = None
) -> Any:
    command = ["kubectl"]
    if args.kubeconfig:
        command.extend(["--kubeconfig", args.kubeconfig])
    if namespace:
        command.extend(["-n", namespace])
    command.extend(cmd)
    command.extend(["-o", "json"])

    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise CheckError(
            f"kubectl command failed (cmd={' '.join(command)}): {result.stderr.strip() or result.stdout.strip()}"
        )
    return json.loads(result.stdout)


def ensure_namespace_exists(args: argparse.Namespace, namespace: str) -> None:
    run_kubectl_json(args, ["get", "namespace", namespace])


def ensure_equal(actual: Any, expected: Any, message: str) -> None:
    if actual != expected:
        raise CheckError(f"{message}: expected {expected!r}, got {actual!r}")


class CheckReporter:
    """Utility for printing status information for each check."""

    SUCCESS_ICON = "\033[92m✔\033[0m"
    FAILURE_ICON = "\033[91m✘\033[0m"

    def check(self, description: str, func: Callable[[], None]) -> None:
        try:
            func()
        except Exception as exc:
            print(f"{self.FAILURE_ICON} {description}: failed ({exc})")
            raise
        else:
            print(f"{self.SUCCESS_ICON} {description}: succeeded")


def validate_ingress(args: argparse.Namespace, reporter: CheckReporter) -> None:
    ingress: dict[str, Any] | None = None
    host_rule: dict[str, Any] | None = None
    matching_path: dict[str, Any] | None = None
    backend_service: dict[str, Any] | None = None

    reporter.check(
        f"Namespace '{NAMESPACE}' exists",
        lambda: ensure_namespace_exists(args, NAMESPACE),
    )

    def fetch_ingress() -> None:
        nonlocal ingress
        ingress = run_kubectl_json(
            args, ["get", "ingress", INGRESS_NAME], namespace=NAMESPACE
        )

    reporter.check(f"Ingress '{INGRESS_NAME}' exists", fetch_ingress)

    def ensure_host_rule() -> None:
        nonlocal host_rule
        if ingress is None:
            raise CheckError("Ingress resource is unavailable")
        spec = ingress.get("spec", {})
        rules = spec.get("rules", [])
        if not rules:
            raise CheckError("Ingress must define at least one rule")
        host_rule = next((rule for rule in rules if rule.get("host") == EXPECTED_HOST), None)
        if not host_rule:
            raise CheckError(f"Ingress must define a rule for host '{EXPECTED_HOST}'")

    reporter.check(
        f"Ingress defines host rule for '{EXPECTED_HOST}'",
        ensure_host_rule,
    )

    def ensure_path_rule() -> None:
        nonlocal matching_path
        if host_rule is None:
            raise CheckError("Host rule is unavailable")
        http_rule = host_rule.get("http") or {}
        paths = http_rule.get("paths", [])
        matching_path = next(
            (
                path
                for path in paths
                if path.get("path") == EXPECTED_PATH
                and path.get("pathType") == EXPECTED_PATHTYPE
            ),
            None,
        )
        if not matching_path:
            raise CheckError(
                f"Host rule must include path '{EXPECTED_PATH}' with pathType '{EXPECTED_PATHTYPE}'"
            )

    reporter.check(
        f"Host rule routes path '{EXPECTED_PATH}' with pathType '{EXPECTED_PATHTYPE}'",
        ensure_path_rule,
    )

    def ensure_backend_service() -> None:
        nonlocal backend_service
        if matching_path is None:
            raise CheckError("Ingress path definition is unavailable")
        backend_service = matching_path.get("backend", {}).get("service")
        if not backend_service:
            raise CheckError("Ingress path must forward to a backend Service")
        service_name = backend_service.get("name")
        ensure_equal(
            service_name,
            EXPECTED_SERVICE,
            f"Ingress must point to Service '{EXPECTED_SERVICE}'",
        )

    reporter.check(
        f"Ingress routes traffic to Service '{EXPECTED_SERVICE}'",
        ensure_backend_service,
    )

    def ensure_backend_port() -> None:
        if backend_service is None:
            raise CheckError("Ingress backend service is unavailable")
        port_info = backend_service.get("port", {})
        port_number = port_info.get("number")
        ensure_equal(
            port_number,
            EXPECTED_SERVICE_PORT,
            f"Ingress backend must use Service port {EXPECTED_SERVICE_PORT}",
        )

    reporter.check(
        f"Ingress backend uses Service port {EXPECTED_SERVICE_PORT}",
        ensure_backend_port,
    )


def run_checks(args: argparse.Namespace) -> None:
    reporter = CheckReporter()
    validate_ingress(args, reporter)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        run_checks(args)
    except CheckError as exc:
        print(f"[ERROR] {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[ERROR] Unexpected failure: {exc}")
        return 1
    else:
        print("All checks passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
