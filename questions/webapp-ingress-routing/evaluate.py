#!/usr/bin/env python3
"""Validation script for the "Web App Ingress Routing" question."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, List, Sequence

QUESTIONS_DIR = Path(__file__).resolve().parents[1]
if str(QUESTIONS_DIR) not in sys.path:
    sys.path.insert(0, str(QUESTIONS_DIR))

from lib.checks import (  # noqa: E402
    CheckError,
    CheckReporter,
    ensure_equal,
    ensure_namespace_exists,
    run_kubectl_json,
)

NAMESPACE = "ingress-ns"
INGRESS_NAME = "webapp-ingress"
EXPECTED_HOST = "webapp.practice.local"
EXPECTED_SERVICE = "webapp-svc"
EXPECTED_PATH = "/"
EXPECTED_PATHTYPE = "Prefix"
EXPECTED_SERVICE_PORT = 80


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the webapp ingress configuration")
    parser.add_argument(
        "--kubeconfig",
        default=None,
        help="Path to the kubeconfig file (defaults to $KUBECONFIG or ~/.kube/config)",
    )
    return parser.parse_args(argv)


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
    reporter.raise_for_failures()


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
