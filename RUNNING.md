Koral — Minikube run instructions

Build and load the Docker image into Minikube (no remote registry):

```bash
docker build -t koral:v1 .
minikube image load koral:v1
```

Apply Kubernetes manifests:

```bash
kubectl apply -f k8s/koral-deployment.yaml
kubectl apply -f k8s/koral-service.yaml
```

Access the service (Minikube):

```bash
# Option A: use kubectl to get NodePort and minikube IP
kubectl get svc koral
minikube ip
# then open http://<MINIKUBE_IP>:30080

# Option B: use minikube service helper
minikube service koral --url
```

Troubleshooting
- ImagePullBackOff
  - Cause: Kubernetes tried to pull the image from a registry.
  - Check: `kubectl describe pod <pod>` and `kubectl get events`.
  - Fixes:
    - Confirm you built the image locally: `docker images | grep koral`.
    - Load image into Minikube: `minikube image load koral:v1` and then restart the pod or reapply the deployment.
    - Ensure `imagePullPolicy: Never` is set in `k8s/koral-deployment.yaml` (we set this).

- Pod not starting / CrashLoopBackOff
  - Check logs: `kubectl logs <pod> -c koral`.
  - Check events and describe: `kubectl describe pod <pod>` for mounts, env, or permission errors.
  - Common fixes:
    - Missing files: ensure the Dockerfile copied the application files needed (we copy `backend/`, `feedback/`, and `threshold/`).
    - Dependency build failures: rebuild image and watch `docker build` output for pip errors.
    - Permission errors: Dockerfile creates a non-root `appuser`; if the app needs root, adjust accordingly.

- Port not accessible
  - Verify container port: container listens on port 8000 (uvicorn). Deployment uses containerPort: 8000.
  - Verify service mapping: `kubectl get svc koral` shows `PORT(S)` and `NODE-PORT` (30080).
  - Confirm minikube IP and nodePort (example URL: `http://<MINIKUBE_IP>:30080`).
  - Alternatively: `minikube service koral --url` returns a working URL.

Notes & consistency
- Image name: `koral:v1` (must be exact).
- Container name: `koral` (in Deployment manifest).
- Deployment name: `koral`.
