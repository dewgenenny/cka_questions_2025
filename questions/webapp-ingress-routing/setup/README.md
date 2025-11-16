# Setup Instructions

The manifests in this directory bootstrap the namespace, Deployment, and
Service required for the "Web App Ingress Routing" exercise.

## Apply the Resources

```bash
kubectl apply -f manifests/webapp.yaml
```

This command creates:

- Namespace `ingress-ns`
- Deployment `webapp-deploy` (serves a simple nginx page)
- ClusterIP Service `webapp-svc` exposing the Deployment on port 80

## Cleanup (Optional)

If you want to remove the resources after practicing, run:

```bash
kubectl delete -f manifests/webapp.yaml
```
