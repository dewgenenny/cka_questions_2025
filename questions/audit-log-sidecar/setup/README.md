# Setup Instructions

Apply the provided namespace manifest so that the `observability-ns` namespace
exists before attempting the question:

```bash
kubectl apply -f observability-namespace.yaml
```

When you are finished with the exercise, remove the namespace (and all resources
inside it) with:

```bash
kubectl delete namespace observability-ns
```
