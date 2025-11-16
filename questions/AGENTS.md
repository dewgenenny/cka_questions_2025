# Evaluator authoring guidelines

All evaluator scripts that live anywhere under the `questions/` directory must
follow these rules:

1. **Shared helpers** – Import checking helpers from
   `questions/lib/checks.py` (via `lib.checks`). This guarantees consistent
   behavior across all questions.
2. **Complete execution** – Always run every declared check before exiting. Use
   the shared `CheckReporter` and call `raise_for_failures()` after registering
   your checks so that failures are reported collectively instead of stopping
   at the first error.
3. **New helpers** – If additional generic helpers are needed, add them to
   `questions/lib/checks.py` so future evaluators can reuse the same behavior.

These conventions keep the evaluator UX uniform and make it easy for authors to
extend the toolset without duplicating logic.
