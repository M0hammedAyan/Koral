# Infrastructure Tools

This file lists the non-Python tools used to run, validate, and deploy KORAL.

These tools must not be added to `requirements.txt` because they are not Python packages.

## Required tools

- Docker
- Terraform
- kubectl
- Helm
- Minikube, if you use local Kubernetes development

## Notes

- Python service dependencies belong in service-level `requirements.txt` files such as `backend/requirements.txt`.
- CI workflows install Python dependencies separately from system or cluster tooling.