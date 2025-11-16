#!/usr/bin/env python3
"""Skeleton evaluator for CKA practice questions.

Copy this file into a new question directory and replace the placeholder logic
inside `run_checks` with validations that make sense for your scenario.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

QUESTIONS_DIR = Path(__file__).resolve().parents[1]
if str(QUESTIONS_DIR) not in sys.path:
    sys.path.insert(0, str(QUESTIONS_DIR))

from lib.checks import CheckError, CheckReporter  # noqa: E402


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the question outcome")
    parser.add_argument(
        "--kubeconfig",
        default=None,
        help="Path to the kubeconfig file (defaults to value of $KUBECONFIG or ~/.kube/config)",
    )
    return parser.parse_args(argv)


def run_checks(args: argparse.Namespace) -> None:
    """Replace this stub with real validation logic.

    Example ideas:
      * Use the Kubernetes Python client to verify resources.
      * Inspect files, logs, or command output.
      * Perform HTTP checks against cluster services.
    """

    reporter = CheckReporter()

    def placeholder_check() -> None:
        raise NotImplementedError("Implement run_checks() for your question")

    reporter.check("Placeholder check", placeholder_check)
    reporter.raise_for_failures()


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        run_checks(args)
    except CheckError as exc:
        print(f"[ERROR] {exc}")
        return 1
    except NotImplementedError as exc:  # pragma: no cover - placeholder behavior
        print(f"[ERROR] {exc}")
        return 2
    except Exception as exc:  # pragma: no cover - future authors can customize
        print(f"[ERROR] Unexpected failure: {exc}")
        return 1
    else:
        print("All checks passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
