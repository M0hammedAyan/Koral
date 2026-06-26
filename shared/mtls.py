"""
KORAL mTLS Helper — Shared module for mutual TLS between services.

When MTLS_ENABLED=true, this module:
  1. Provides SSL context for uvicorn to serve HTTPS
  2. Provides an httpx client factory with client certificates for outbound calls
  3. Validates peer certificates against the internal CA

Usage in any service:

    from shared.mtls import get_ssl_context, get_mtls_client, is_mtls_enabled

    # Server-side (pass to uvicorn)
    if is_mtls_enabled():
        ssl_ctx = get_ssl_context()
        uvicorn.run(app, host="0.0.0.0", port=8000, ssl_keyfile=..., ssl_certfile=...)

    # Client-side (outbound calls)
    async with get_mtls_client() as client:
        resp = await client.get("https://backend:8000/health")
"""

import os
import ssl
from typing import Optional

import httpx

# Environment variables set by Helm when mtls.enabled=true
MTLS_ENABLED = os.getenv("MTLS_ENABLED", "false").lower() == "true"
TLS_CERT_PATH = os.getenv("TLS_CERT_PATH", "/etc/koral/certs/tls.crt")
TLS_KEY_PATH = os.getenv("TLS_KEY_PATH", "/etc/koral/certs/tls.key")
TLS_CA_PATH = os.getenv("TLS_CA_PATH", "/etc/koral/ca/ca.crt")


def is_mtls_enabled() -> bool:
    """Check if mTLS is enabled via environment."""
    return MTLS_ENABLED


def get_ssl_context(purpose: str = "server") -> Optional[ssl.SSLContext]:
    """
    Build an SSL context for mTLS.

    Args:
        purpose: "server" for uvicorn, "client" for outbound calls.

    Returns:
        ssl.SSLContext configured for mutual TLS, or None if mTLS is disabled.
    """
    if not MTLS_ENABLED:
        return None

    if purpose == "server":
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.verify_mode = ssl.CERT_REQUIRED  # Require client cert
    else:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    # Load our certificate and private key
    ctx.load_cert_chain(certfile=TLS_CERT_PATH, keyfile=TLS_KEY_PATH)

    # Load CA to verify peer certificates
    ctx.load_verify_locations(cafile=TLS_CA_PATH)

    # Security hardening
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.set_ciphers(
        "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
    )

    return ctx


def get_service_url(service: str, port: int) -> str:
    """
    Get the appropriate URL scheme for a service based on mTLS config.

    Args:
        service: Service hostname (e.g., "backend", "ai-engine")
        port: Service port number

    Returns:
        Full URL with https:// if mTLS enabled, http:// otherwise.
    """
    scheme = "https" if MTLS_ENABLED else "http"
    return f"{scheme}://{service}:{port}"


def get_mtls_client(timeout: float = 10.0) -> httpx.AsyncClient:
    """
    Create an httpx.AsyncClient configured for mTLS outbound calls.

    If mTLS is disabled, returns a plain HTTP client.

    Usage:
        async with get_mtls_client() as client:
            resp = await client.get(url)
    """
    if not MTLS_ENABLED:
        return httpx.AsyncClient(timeout=timeout)

    ssl_ctx = get_ssl_context(purpose="client")
    return httpx.AsyncClient(verify=ssl_ctx, timeout=timeout)


def get_uvicorn_ssl_kwargs() -> dict:
    """
    Get kwargs to pass to uvicorn.run() for TLS server mode.

    Returns:
        Dict with ssl_keyfile, ssl_certfile, ssl_ca_certs if mTLS enabled,
        otherwise empty dict.
    """
    if not MTLS_ENABLED:
        return {}

    return {
        "ssl_keyfile": TLS_KEY_PATH,
        "ssl_certfile": TLS_CERT_PATH,
        "ssl_ca_certs": TLS_CA_PATH,
        "ssl_cert_reqs": ssl.CERT_REQUIRED,
    }
