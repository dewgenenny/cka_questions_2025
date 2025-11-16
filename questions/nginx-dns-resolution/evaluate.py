#!/usr/bin/env python3
"""Validation script for the "Nginx DNS Resolver Checks" question."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, List

QUESTIONS_DIR = Path(__file__).resolve().parents[1]
if str(QUESTIONS_DIR) not in sys.path:
    sys.path.insert(0, str(QUESTIONS_DIR))

from lib.checks import (  # noqa: E402  (import after sys.path mutation)
    CheckError,
    CheckReporter,
    ensure_equal,
    run_kubectl_json,
)

SERVICE_OUTPUT = Path("/root/CKA/nginx.svc")
POD_OUTPUT = Path("/root/CKA/nginx.pod")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the DNS resolver exercise")
    parser.add_argument(
        "--kubeconfig",
        default=None,
        help="Path to the kubeconfig file (defaults to $KUBECONFIG or ~/.kube/config)",
    )
    return parser.parse_args(argv)


def load_file(path: Path) -> str:
    if not path.exists():
        raise CheckError(f"Required file {path} does not exist")
    contents = path.read_text().strip()
    if not contents:
        raise CheckError(f"File {path} is empty; expected nslookup output")
    return contents


def ensure_service_port(service: dict[str, Any], port: int) -> None:
    ports = service.get("spec", {}).get("ports", [])
    for service_port in ports:
        if service_port.get("port") == port:
            return
    raise CheckError(f"Service must expose port {port}")


def run_checks(args: argparse.Namespace) -> None:
    reporter = CheckReporter()

    pod: dict[str, Any] | None = None
    service: dict[str, Any] | None = None

    def check_pod_exists() -> None:
        nonlocal pod
        pod = run_kubectl_json(args, ["get", "pod", "nginx-resolver"])
        phase = pod.get("status", {}).get("phase")
        if phase != "Running":
            raise CheckError("Pod 'nginx-resolver' must be in Running phase")

    reporter.check("Pod 'nginx-resolver' is running", check_pod_exists)

    def check_pod_image() -> None:
        if pod is None:
            raise CheckError("Pod details unavailable")
        containers = pod.get("spec", {}).get("containers", [])
        if not containers:
            raise CheckError("Pod must define at least one container")
        ensure_equal(
            containers[0].get("image"),
            "nginx",
            "nginx-resolver pod must use the nginx image",
        )

    reporter.check("Pod uses the nginx image", check_pod_image)

    def check_service_exists() -> None:
        nonlocal service
        service = run_kubectl_json(args, ["get", "service", "nginx-resolver-service"])
        service_type = service.get("spec", {}).get("type", "ClusterIP")
        ensure_equal(
            service_type,
            "ClusterIP",
            "Service must be of type ClusterIP",
        )
        ensure_service_port(service, 80)

    reporter.check("Service 'nginx-resolver-service' exposes port 80", check_service_exists)

    def check_service_file() -> None:
        contents = load_file(SERVICE_OUTPUT)
        if "nginx-resolver-service" not in contents:
            raise CheckError(
                "Service lookup output must mention 'nginx-resolver-service'"
            )

    reporter.check("Service DNS lookup saved to /root/CKA/nginx.svc", check_service_file)

    def check_pod_file() -> None:
        if pod is None:
            raise CheckError("Pod details unavailable")
        pod_ip = pod.get("status", {}).get("podIP")
        if not pod_ip:
            raise CheckError("Unable to determine Pod IP for dns lookup validation")
        dns_name = f"{pod_ip.replace('.', '-')}\.default.pod"
        contents = load_file(POD_OUTPUT)
        if dns_name not in contents:
            raise CheckError(
                f"Pod lookup output must reference '{dns_name}'"
            )

    reporter.check("Pod DNS lookup saved to /root/CKA/nginx.pod", check_pod_file)

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
