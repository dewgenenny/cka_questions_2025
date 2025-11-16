# Question Title (Replace Me)

## Scenario

Describe the situation the candidate faces. Mention existing cluster state,
available namespaces, relevant context, and the desired outcome.

## Tasks

1. List actionable steps or goals (e.g. "Create a Deployment named ...").
2. Clearly state the acceptance criteria that the evaluation script will verify.

## Setup

All manifests and helper scripts needed to prepare the exercise live under
[`setup/`](./setup). Document how to apply or tear them down in
[`setup/README.md`](./setup/README.md).

## Evaluation

Run the automated checker after attempting the question:

```bash
python3 evaluate.py
```

The script should exit with status code `0` when the solution is correct, and a
non-zero code otherwise.
