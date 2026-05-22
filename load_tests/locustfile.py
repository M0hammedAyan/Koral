from __future__ import annotations

import os
import random

from locust import HttpUser, between, task


TARGET_USERS = (100, 500, 1000)


class KoralBackendUser(HttpUser):
	wait_time = between(1, 3)
	host = os.getenv("BASE_URL", "http://localhost:8000")

	@task(5)
	def health(self):
		response = self.client.get("/health", timeout=5)
		assert response.status_code in (200, 503)

	@task(3)
	def incidents(self):
		response = self.client.get("/incidents?limit=5", timeout=5)
		assert response.status_code == 200

	@task(1)
	def metrics(self):
		response = self.client.get("/metrics", timeout=5)
		assert response.status_code == 200

	@task(1)
	def ready(self):
		response = self.client.get("/health/ready", timeout=5)
		assert response.status_code in (200, 503)

	@task(1)
	def websocket_probe(self):
		# Lightweight probe of the websocket endpoint path without holding sockets open.
		response = self.client.get("/ws/live", timeout=5, allow_redirects=False)
		assert response.status_code in (200, 400, 404, 405, 426)
