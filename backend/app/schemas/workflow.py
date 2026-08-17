from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class WorkflowResponse(BaseModel):
    item_id: int
    workflow_status: str
    match_candidates_count: int
    match_score: float
    confidence: str
    recommendation: str
    best_match: Optional[Dict[str, Any]] = None
    verification_status: Optional[str] = None
    verification_questions: List[Dict[str, Any]] = []
    verification_score: Optional[float] = None
    verification_evaluation: Optional[str] = None
    admin_review_payload: Optional[Dict[str, Any]] = None
    errors: List[str] = []


class WorkflowVerificationSubmission(BaseModel):
    answers: List[Dict[str, Any]]
