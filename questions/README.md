# Question Authoring Guide

Every practice question lives under `questions/<question-name>` and must include:

1. `README.md` – the scenario, acceptance criteria, and any environment notes.
2. `setup/` – Kubernetes manifests, Helm charts, scripts, or other assets
   required to provision the starting state for the exercise.
3. `evaluate.py` – a Python script that validates the candidate's solution.

## Naming

* Use kebab-case folder names that summarize the task (e.g. `nginx-canary`).
* Keep question titles concise and unique.

## Evaluation Script Requirements

* Must be executable with `python3 evaluate.py` from within the question folder.
* Should exit with code `0` on success and a non-zero code on failure.
* Should print actionable feedback for the learner (e.g. missing resource names).
* Prefer using the official Kubernetes Python client (`kubernetes` module) when
  interacting with a cluster. Include any additional dependencies in a
  `requirements.txt` file inside the same folder.

## Setup Assets

Place all manifests and helper files required to bootstrap the exercise in the
`setup/` directory. Consider providing:

* `setup/README.md` – steps to apply/remove the manifests.
* `setup/manifests/*.yaml` – Kubernetes objects for the initial state.
* `setup/scripts/*.sh` – optional helper scripts (make sure they are executable).

## Suggested Workflow

1. Duplicate `questions/question-template` into a new folder.
2. Update its contents to match your scenario.
3. Test the `evaluate.py` script against both failing and passing states.
4. Submit the changes via pull request.
