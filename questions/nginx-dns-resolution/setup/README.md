# Setup Instructions

No additional manifests are required for this scenario. Work directly in the
cluster's `default` namespace. If you need to reset the environment, delete any
resources you created during the exercise:

```bash
kubectl delete pod nginx-resolver
kubectl delete service nginx-resolver-service
rm -f /root/CKA/nginx.svc /root/CKA/nginx.pod
```
