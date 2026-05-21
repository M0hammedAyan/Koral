# Development Infrastructure Tools

This repository requires several non-Python CLI tools to run the Kubernetes-based local/deploy workflows.

Install via `scripts/setup-infra.sh` or manually following upstream docs:

- minikube (local Kubernetes cluster)
- kubectl (Kubernetes CLI)
- helm (Kubernetes package manager)

Do NOT include these tools in any `requirements.txt` used by `pip`.
