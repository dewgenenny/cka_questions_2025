# CKA Practice Questions 2025

This repository hosts a collection of hands-on Kubernetes Administrator (CKA) practice
questions. Each exercise lives in its own folder with:

* A self-contained infrastructure setup (YAML manifests, Helm charts, helper scripts, etc.).
* Clear instructions for the candidate.
* A Python-based evaluation script that validates the expected outcome.

## Repository Layout

```
questions/
  question-template/   # Boilerplate for new questions
  <question-name>/     # Concrete tasks will be added here
```

See [`questions/README.md`](questions/README.md) for detailed conventions and
guidance on how to contribute new questions.

## Workflow for Adding a Question

1. Copy the `questions/question-template` folder to a new directory whose name
   briefly describes the scenario, e.g. `backup-etcd-snapshot`.
2. Update the `README.md` inside the new folder with the actual problem
   statement and any setup/cleanup instructions.
3. Provide the Kubernetes manifests, scripts, or other infrastructure assets
   required to attempt the question (place them under `setup/`).
4. Implement the `evaluate.py` script to assert the expected cluster state.
5. Document any environment assumptions in the question README and keep
   everything reproducible.

Once the structure is in place, individual questions can be added via pull
requests following the same conventions.

## Available Practice Scenarios

- [Audit Log Sidecar Streaming](questions/audit-log-sidecar/README.md)
- [Web App Ingress Routing](questions/webapp-ingress-routing/README.md)
