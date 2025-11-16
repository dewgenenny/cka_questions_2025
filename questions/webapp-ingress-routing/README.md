# Web App Ingress Routing

## Scenario

A namespace named `ingress-ns` already hosts a Deployment (`webapp-deploy`) that
serves a simple HTTP site and is exposed internally via the ClusterIP Service
`webapp-svc` (port 80). The cluster also has a functional Ingress controller
(such as ingress-nginx). You are asked to publish the application through an
Ingress object that performs host-based routing.

## Tasks

1. Create an Ingress resource called `webapp-ingress` in the `ingress-ns`
   namespace.
2. Configure the Ingress with a single rule for the host
   `webapp.practice.local`.
3. Route requests for the path `/` (with `pathType: Prefix`) to the backend
   Service `webapp-svc` on port `80`.
4. Ensure the rule directs traffic to the Service without modifying the path.

## Testing the Result

Once the Ingress is in place, determine the address of your Ingress controller
(e.g., `minikube ip`, the load balancer IP, or a Node IP/port-forward). Use
`curl` with the `--resolve` flag to test host-based routing without modifying
`/etc/hosts`:

```bash
INGRESS_IP=<replace-with-ingress-address>
curl -s --resolve webapp.practice.local:80:${INGRESS_IP} http://webapp.practice.local/
```

If everything is configured correctly, the command should return the welcome
page served by the `webapp-deploy` Pods.

## Setup

All manifests required to provision the starting point for this exercise are in
[`setup/`](./setup). Apply them before attempting the task.

## Evaluation

Run the automated checker after completing the task:

```bash
python3 evaluate.py
```

The script exits with status code `0` when the solution is correct and a
non-zero value otherwise.
