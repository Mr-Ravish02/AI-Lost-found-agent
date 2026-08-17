from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class AdminStatsResponse(BaseModel):
    total_lost: int
    total_found: int
    potential_matches: int
    pending_reviews: int
    resolved_cases: int


class AdminActionRequest(BaseModel):
    notes: Optional[str] = None
    reason: Optional[str] = None


class AdminMatchSummary(BaseModel):
    match_id: int
    lost_item: Dict[str, Any]
    found_item: Dict[str, Any]
    match_score: float
    confidence_level: str
    factor_breakdown: Optional[Dict[str, Any]] = None
    reasons: List[str] = []
    status: str
    verification_score: Optional[float] = None
    verification_evaluation: Optional[str] = None
    answers_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AdminMatchDetailResponse(BaseModel):
    match_id: int
    lost_item: Dict[str, Any]
    found_item: Dict[str, Any]
    match_score: float
    confidence_level: str
    factor_breakdown: Optional[Dict[str, Any]] = None
    reasons: List[str] = []
    status: str
    admin_notes: Optional[str] = None
    verification_score: Optional[float] = None
    verification_evaluation: Optional[str] = None
    questions: List[Dict[str, Any]] = []
    answers: List[Dict[str, Any]] = []
    admin_actions: List[Dict[str, Any]] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class NotificationOut(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    type: str
    link: Optional[str] = None
    is_read: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
