from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class MatchFactorBreakdown(BaseModel):
    text: Optional[float] = None
    category: Optional[float] = None
    location: Optional[float] = None
    color: Optional[float] = None
    brand: Optional[float] = None
    date: Optional[float] = None
    features: Optional[float] = None


class MatchItemSummary(BaseModel):
    id: int
    type: str
    title: str
    category: str
    description: str
    location: str
    color: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    date_lost: Optional[str] = None
    date_found: Optional[str] = None
    distinctive_features: Optional[Any] = None
    image_url: Optional[str] = None
    status: str
    user_name: Optional[str] = None


class MatchEntryOut(BaseModel):
    match_id: int
    lost_item: Optional[MatchItemSummary] = None
    candidate_item: MatchItemSummary
    match_score: float
    confidence: str
    factors: MatchFactorBreakdown
    reasons: List[str]
    status: str


class MatchAnalysisResponse(BaseModel):
    source_item: MatchItemSummary
    total_candidates_analyzed: int
    matches_count: int
    top_match: Optional[MatchEntryOut] = None
    matches: List[MatchEntryOut]


class MatchDetailOut(BaseModel):
    id: int
    lost_item_id: int
    found_item_id: int
    match_score: float
    confidence_level: str
    factor_breakdown: Optional[Dict[str, Any]] = None
    reasons: Optional[List[str]] = None
    status: str
    admin_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    lost_item: Optional[MatchItemSummary] = None
    found_item: Optional[MatchItemSummary] = None

    class Config:
        from_attributes = True
