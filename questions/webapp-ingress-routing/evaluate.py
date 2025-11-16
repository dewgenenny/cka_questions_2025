#!/usr/bin/env python3
"""Validation script for the "Web App Ingress Routing" question."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, List, Sequence

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


def run_kubectl_json(args: argparse.Namespace, cmd: Sequence[str]) -> Any:
    command = ["kubectl"]
    if args.kubeconfig:
        command.extend(["--kubeconfig", args.kubeconfig])
    command.extend(["-n", NAMESPACE])
    command.extend(cmd)
    command.extend(["-o", "json"])

    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise CheckError(
            f"kubectl command failed (cmd={' '.join(command)}): {result.stderr.strip() or result.stdout.strip()}"
        )
    return json.loads(result.stdout)


def validate_ingress(args: argparse.Namespace) -> None:
    ingress = run_kubectl_json(args, ["get", "ingress", INGRESS_NAME])
    spec = ingress.get("spec", {})
    rules = spec.get("rules", [])
    if not rules:
        raise CheckError("Ingress must define at least one rule")

    host_rule = next((rule for rule in rules if rule.get("host") == EXPECTED_HOST), None)
    if not host_rule:
        raise CheckError(f"Ingress must define a rule for host '{EXPECTED_HOST}'")

    http_rule = host_rule.get("http") or {}
    paths = http_rule.get("paths", [])
    matching_path = None
    for path in paths:
        if path.get("path") == EXPECTED_PATH and path.get("pathType") == EXPECTED_PATHTYPE:
            matching_path = path
            break

    if not matching_path:
        raise CheckError(
            f"Host rule must include path '{EXPECTED_PATH}' with pathType '{EXPECTED_PATHTYPE}'"
        )

    backend = matching_path.get("backend", {}).get("service")
    if not backend:
        raise CheckError("Ingress path must forward to a backend Service")

    service_name = backend.get("name")
    if service_name != EXPECTED_SERVICE:
        raise CheckError(
            f"Ingress must point to Service '{EXPECTED_SERVICE}' (found: '{service_name}')"
        )

    port_info = backend.get("port", {})
    port_number = port_info.get("number")
    if port_number != EXPECTED_SERVICE_PORT:
        raise CheckError(
            f"Ingress backend must use Service port {EXPECTED_SERVICE_PORT} (found: {port_number})"
        )


def run_checks(args: argparse.Namespace) -> None:
    validate_ingress(args)


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
