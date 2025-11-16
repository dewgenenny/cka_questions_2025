#!/usr/bin/env python3
"""Validation script for the "Audit Log Sidecar Streaming" question."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, List, Sequence


@dataclass
class CheckError(Exception):
    message: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the audit sidecar deployment")
    parser.add_argument(
        "--kubeconfig",
        default=None,
        help="Path to the kubeconfig file (defaults to $KUBECONFIG or ~/.kube/config)",
    )
    return parser.parse_args(argv)


def run_kubectl_json(args: argparse.Namespace, cmd: Sequence[str], namespace: str | None = None) -> Any:
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
        normalized.append(" ".join(value.split()))
    return normalized


def ensure_command(container: dict, expected: Sequence[str], message: str) -> None:
    actual_command = container_command(container)
    normalized_actual = normalize_command_tokens(actual_command)
    normalized_expected = normalize_command_tokens(expected)
    if normalized_actual != normalized_expected:
        raise CheckError(
            f"{message}: expected {list(expected)!r}, got {actual_command!r}"
        )


def validate_deployment(args: argparse.Namespace) -> None:
    namespace = "observability-ns"
    deployment_name = "audit-stream"
    ensure_namespace_exists(args, namespace)

    deployment = run_kubectl_json(args, ["get", "deployment", deployment_name], namespace=namespace)

    replicas = deployment.get("spec", {}).get("replicas")
    ensure_equal(replicas, 1, "Deployment must have exactly 1 replica")

    pod_spec = deployment.get("spec", {}).get("template", {}).get("spec", {})
    volumes = pod_spec.get("volumes", [])
    audit_volume = next((vol for vol in volumes if vol.get("name") == "audit-storage"), None)
    if not audit_volume:
        raise CheckError("Pod template must define an emptyDir volume named 'audit-storage'")
    if "emptyDir" not in audit_volume:
        raise CheckError("Volume 'audit-storage' must be of type emptyDir")

    containers = pod_spec.get("containers", [])
    writer = find_container(containers, "audit-writer")
    tail_agent = find_container(containers, "tail-agent")

    ensure_equal(writer.get("image"), "busybox", "audit-writer must use the busybox image")
    ensure_command(
        writer,
        ["sh", "-c", "while true; do date >> /var/audit/audit.log; sleep 3; done"],
        "audit-writer command is incorrect",
    )
    if not has_volume_mount(writer, "audit-storage", "/var/audit"):
        raise CheckError("audit-writer must mount volume 'audit-storage' at /var/audit")

    ensure_equal(tail_agent.get("image"), "busybox", "tail-agent must use the busybox image")
    ensure_command(
        tail_agent,
        ["sh", "-c", "tail -n+1 -f /var/audit/audit.log"],
        "tail-agent command is incorrect",
    )
    if not has_volume_mount(tail_agent, "audit-storage", "/var/audit"):
        raise CheckError("tail-agent must mount volume 'audit-storage' at /var/audit")


def run_checks(args: argparse.Namespace) -> None:
    validate_deployment(args)


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
