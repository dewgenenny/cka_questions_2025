# Audit Log Sidecar Streaming

## Scenario

The observability team has provisioned a dedicated namespace called
`observability-ns` for experimenting with different log shipping patterns. They
would like to confirm that you can implement a classic sidecar pattern where a
primary container writes structured logs to disk and a second container streams
those logs for collection.

Before starting, apply the manifests under [`setup/`](./setup) to ensure the
namespace is available.

## Tasks

1. In the `observability-ns` namespace, create a Deployment named
   `audit-stream` with **one replica**.
2. The pod must contain two containers that share the same `emptyDir` volume:
   - `audit-writer`: uses the `busybox` image and runs the exact command
     `sh -c "while true; do date >> /var/audit/audit.log; sleep 3; done"`.
     This container is responsible for continuously appending timestamped
     entries to `/var/audit/audit.log`.
   - `tail-agent`: also uses the `busybox` image and runs
     `sh -c "tail -n+1 -f /var/audit/audit.log"` so that it streams whatever
     `audit-writer` writes.
3. Mount the shared `emptyDir` volume (name it `audit-storage`) at
   `/var/audit` inside **both** containers so they operate on the same log file.

## Acceptance Criteria

The evaluation script will verify the following:

- Namespace `observability-ns` exists.
- Deployment `audit-stream` is present in that namespace with exactly one
  replica.
- Pod spec defines an `emptyDir` volume named `audit-storage` that is mounted at
  `/var/audit` by both containers.
- Containers are named `audit-writer` and `tail-agent`, use the `busybox` image,
  and run the commands listed above.

## Evaluation

After completing the task, run the checker from this directory:

```bash
python3 evaluate.py
```

It should report `All checks passed!` when your solution meets the criteria.
