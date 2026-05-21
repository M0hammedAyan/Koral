def standard_response(status: str, code: int, request_id: str, message: str, details: str = "") -> dict:
    return {
        "status": status,
        "code": code,
        "request_id": request_id,
        "message": message,
        "details": details,
    }
