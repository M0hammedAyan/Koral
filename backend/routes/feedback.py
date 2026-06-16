from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.rbac import require_operator

router = APIRouter()


class FeedbackPayload(BaseModel):
    incident_id: str
    metric: str
    is_correct: bool


@router.post("/feedback", status_code=200, dependencies=[Depends(require_operator)])
def receive_feedback(payload: FeedbackPayload):
    try:
        from feedback.feedback_loop import process_feedback
        record = process_feedback(payload.incident_id, payload.metric, payload.is_correct)
        return {"status": "applied", "adjustment": record}
    except Exception as e:
        return {"status": "feedback_loop_unavailable", "detail": str(e)}
