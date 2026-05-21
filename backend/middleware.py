from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
import uuid


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next: Callable):
        # Extract or generate request id
        req_id = request.headers.get("x-request-id") or request.headers.get("X-Request-ID")
        if req_id:
            # Reject duplicate style values containing commas/space
            req_id = req_id.split(",")[0].strip()
        else:
            req_id = uuid.uuid4().hex
        request.state.request_id = req_id

        response: Response = await call_next(request)
        # Attach header for clients and traces
        response.headers["X-Request-ID"] = req_id
        return response


class ErrorResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next: Callable):
        try:
            return await call_next(request)
        except Exception as exc:
            # Minimal safe fallback for uncaught exceptions
            req_id = getattr(request.state, "request_id", None) or ""
            body = {
                "status": "error",
                "code": 500,
                "request_id": req_id,
                "message": "internal_server_error",
                "details": str(exc),
            }
            return Response(content=__import__("json").dumps(body), media_type="application/json", status_code=500)
