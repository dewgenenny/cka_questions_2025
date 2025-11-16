# Nginx DNS Resolver Checks

## Scenario

Cluster networking engineers want proof that every node can resolve both Service
and Pod DNS entries. They have asked you to spin up a simple workload in the
`default` namespace, expose it internally, and capture the results of DNS
lookups from inside the cluster.

## Tasks

1. Create a Pod named `nginx-resolver` that runs the `nginx` container image.
2. Expose the Pod with a ClusterIP Service named `nginx-resolver-service` on
   port `80` so the Pod is reachable via the Service DNS name.
3. Launch a temporary BusyBox (`busybox:1.28`) utility Pod to perform DNS
   lookups:
   - Run `nslookup nginx-resolver-service` and save the command output to
     `/root/CKA/nginx.svc` on the node where you executed the command.
   - Run `nslookup <pod-ip>.default.pod` (replace dots in the Pod IP with
     hyphens per Kubernetes Pod DNS conventions) and save the output to
     `/root/CKA/nginx.pod`.
4. Ensure both files exist on the control plane host and contain the resolver
   output produced by BusyBox.

## Tips

* The fully qualified service name is `nginx-resolver-service.default.svc`. You
  can use the short name inside the default namespace.
* To resolve the Pod directly, format the Pod IP as
  `10-244-0-5.default.pod` (i.e., replace dots with hyphens). That IP is only
  an example—substitute the actual Pod IP address from your cluster.
* Use `kubectl run tmp --rm -it --restart=Never --image=busybox:1.28 --` to run
  disposable DNS lookup Pods.

## Evaluation

After completing the exercise, run the automated checker from this directory:

```bash
python3 evaluate.py
```

It should report `All checks passed!` when the Pod, Service, and DNS evidence
files meet the acceptance criteria.
