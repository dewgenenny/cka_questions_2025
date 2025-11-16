#!/usr/bin/env python3
"""Validation script for the "Audit Log Sidecar Streaming" question."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, List, Sequence

QUESTIONS_DIR = Path(__file__).resolve().parents[1]
if str(QUESTIONS_DIR) not in sys.path:
    sys.path.insert(0, str(QUESTIONS_DIR))

from lib.checks import (  # noqa: E402  (import after sys.path mutation)
    CheckError,
    CheckReporter,
    ensure_equal,
    ensure_namespace_exists,
    run_kubectl_json,
)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the audit sidecar deployment")
    parser.add_argument(
        "--kubeconfig",
        default=None,
        help="Path to the kubeconfig file (defaults to $KUBECONFIG or ~/.kube/config)",
    )
    return parser.parse_args(argv)


def find_container(containers: List[dict], name: str) -> dict:
    for container in containers:
        if container.get("name") == name:
            return container
    raise CheckError(f"Container '{name}' not found in pod template")


def has_volume_mount(container: dict, volume_name: str, mount_path: str) -> bool:
    for mount in container.get("volumeMounts", []):
        if mount.get("name") == volume_name and mount.get("mountPath") == mount_path:
            return True
    return False


def container_command(container: dict) -> List[str]:
    """Return the effective container command (entrypoint + args)."""

    command = container.get("command") or []
    args = container.get("args") or []
    return list(command) + list(args)


def normalize_command_tokens(command: Sequence[str]) -> List[str]:
    """Normalize shell command tokens for easier comparison."""

    normalized: List[str] = []
    for token in command:
        value = token.strip()
        if value in {"/bin/sh", "sh"}:
            normalized.append("sh")
            continue
        collapsed = " ".join(value.split())
        if ";" in collapsed:
            segments = [segment.strip() for segment in collapsed.split(";")]
            collapsed = "; ".join(segment for segment in segments if segment)
        normalized.append(collapsed)
    return normalized


def ensure_command(container: dict, expected: Sequence[str], message: str) -> None:
    actual_command = container_command(container)
    normalized_actual = normalize_command_tokens(actual_command)
    normalized_expected = normalize_command_tokens(expected)
    if normalized_actual != normalized_expected:
        raise CheckError(
            f"{message}: expected {list(expected)!r}, got {actual_command!r}"
        )


def validate_deployment(args: argparse.Namespace, reporter: CheckReporter) -> None:
    namespace = "observability-ns"
    deployment_name = "audit-stream"
    deployment: dict[str, Any] | None = None
    pod_spec: dict[str, Any] | None = None
    writer: dict[str, Any] | None = None
    tail_agent: dict[str, Any] | None = None

    reporter.check(
        "Namespace 'observability-ns' exists",
        lambda: ensure_namespace_exists(args, namespace),
    )

    def fetch_deployment() -> None:
        nonlocal deployment, pod_spec
        deployment = run_kubectl_json(
            args, ["get", "deployment", deployment_name], namespace=namespace
        )
        pod_spec = deployment.get("spec", {}).get("template", {}).get("spec", {})
        if not isinstance(pod_spec, dict):
            raise CheckError("Deployment is missing a pod template spec")

    reporter.check(f"Deployment '{deployment_name}' exists", fetch_deployment)

    def check_replicas() -> None:
        if deployment is None:
            raise CheckError("Deployment has not been loaded")
        replicas = deployment.get("spec", {}).get("replicas")
        ensure_equal(replicas, 1, "Deployment must have exactly 1 replica")

    reporter.check("Deployment has exactly 1 replica", check_replicas)

    def check_audit_volume() -> None:
        if pod_spec is None:
            raise CheckError("Pod spec is unavailable")
        volumes = pod_spec.get("volumes", [])
        audit_volume = next((vol for vol in volumes if vol.get("name") == "audit-storage"), None)
        if not audit_volume:
            raise CheckError("Pod template must define an emptyDir volume named 'audit-storage'")
        if "emptyDir" not in audit_volume:
            raise CheckError("Volume 'audit-storage' must be of type emptyDir")

    reporter.check("Pod template defines emptyDir volume 'audit-storage'", check_audit_volume)

    def ensure_containers_exist() -> None:
        nonlocal writer, tail_agent
        if pod_spec is None:
            raise CheckError("Pod spec is unavailable")
        containers = pod_spec.get("containers", [])
        writer = find_container(containers, "audit-writer")
        tail_agent = find_container(containers, "tail-agent")

    reporter.check("Pod template defines audit-writer and tail-agent containers", ensure_containers_exist)

    def writer_image() -> None:
        if writer is None:
            raise CheckError("audit-writer container not found")
        ensure_equal(writer.get("image"), "busybox", "audit-writer must use the busybox image")

    reporter.check("audit-writer uses the busybox image", writer_image)

    def writer_command() -> None:
        if writer is None:
            raise CheckError("audit-writer container not found")
        ensure_command(
            writer,
            ["sh", "-c", "while true; do date >> /var/audit/audit.log; sleep 3; done"],
            "audit-writer command is incorrect",
        )

    reporter.check("audit-writer writes audit events in a loop", writer_command)

    def writer_volume() -> None:
        if writer is None:
            raise CheckError("audit-writer container not found")
        if not has_volume_mount(writer, "audit-storage", "/var/audit"):
            raise CheckError("audit-writer must mount volume 'audit-storage' at /var/audit")

    reporter.check("audit-writer mounts audit-storage at /var/audit", writer_volume)

    def tail_image() -> None:
        if tail_agent is None:
            raise CheckError("tail-agent container not found")
        ensure_equal(tail_agent.get("image"), "busybox", "tail-agent must use the busybox image")

    reporter.check("tail-agent uses the busybox image", tail_image)

    def tail_command() -> None:
        if tail_agent is None:
            raise CheckError("tail-agent container not found")
        ensure_command(
            tail_agent,
            ["sh", "-c", "tail -n+1 -f /var/audit/audit.log"],
            "tail-agent command is incorrect",
        )

    reporter.check("tail-agent streams the audit log", tail_command)

    def tail_volume() -> None:
        if tail_agent is None:
            raise CheckError("tail-agent container not found")
        if not has_volume_mount(tail_agent, "audit-storage", "/var/audit"):
            raise CheckError("tail-agent must mount volume 'audit-storage' at /var/audit")

    reporter.check("tail-agent mounts audit-storage at /var/audit", tail_volume)


def run_checks(args: argparse.Namespace) -> None:
    reporter = CheckReporter()
    validate_deployment(args, reporter)
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
