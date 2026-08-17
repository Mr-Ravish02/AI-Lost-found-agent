import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.database import get_db
from app.models.user import User
from app.models.item import LostItem, FoundItem, Match
from app.schemas.match import MatchAnalysisResponse, MatchDetailOut, MatchEntryOut
from app.agents.matching_agent import (
    find_matches_for_lost_item,
    find_matches_for_found_item,
    item_to_dict
)
from app.agents.extraction_agent import extract_item_attributes
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI Matching Engine"])


# -----------------------------------------------------------------------------
# Trigger Match Analysis
# -----------------------------------------------------------------------------
@router.post("/match/lost/{lost_item_id}", response_model=MatchAnalysisResponse)
@router.post("/matching/lost/{lost_item_id}", response_model=MatchAnalysisResponse)
def trigger_match_for_lost_item(
    lost_item_id: int,
    min_score: float = Query(35.0, ge=0.0, le=100.0, description="Minimum similarity score threshold"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Triggers the AI Matching Agent to evaluate candidate found items for a given lost item report.
    """
    lost_item = db.query(LostItem).filter(LostItem.id == lost_item_id).first()
    if not lost_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lost item with ID {lost_item_id} not found."
        )

    # Permission check: Owner or admin
    if lost_item.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only trigger match analysis for your own reported items."
        )

    try:
        result = find_matches_for_lost_item(lost_item_id, db, min_score_threshold=min_score)
        return result
    except Exception as exc:
        logger.error(f"Match error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Matching engine encountered an error: {str(exc)}"
        )


@router.post("/match/found/{found_item_id}", response_model=MatchAnalysisResponse)
@router.post("/matching/found/{found_item_id}", response_model=MatchAnalysisResponse)
def trigger_match_for_found_item(
    found_item_id: int,
    min_score: float = Query(35.0, ge=0.0, le=100.0, description="Minimum similarity score threshold"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Triggers the AI Matching Agent to evaluate candidate lost items for a given found item report.
    """
    found_item = db.query(FoundItem).filter(FoundItem.id == found_item_id).first()
    if not found_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Found item with ID {found_item_id} not found."
        )

    if found_item.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only trigger match analysis for your own reported items."
        )

    try:
        result = find_matches_for_found_item(found_item_id, db, min_score_threshold=min_score)
        return result
    except Exception as exc:
        logger.error(f"Match error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Matching engine encountered an error: {str(exc)}"
        )


# -----------------------------------------------------------------------------
# Retrieve Existing Matches
# -----------------------------------------------------------------------------
@router.get("/matches/{item_type}/{item_id}")
def get_existing_matches_for_item(
    item_type: str,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves stored matches for a lost or found item.
    """
    t = item_type.lower().strip()
    if t not in ["lost", "found"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="item_type must be either 'lost' or 'found'."
        )

    if t == "lost":
        item = db.query(LostItem).filter(LostItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Lost item not found")
        if item.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Forbidden")
        
        matches = (
            db.query(Match)
            .filter(Match.lost_item_id == item_id)
            .order_by(desc(Match.match_score))
            .all()
        )
        return [
            {
                "match_id": m.id,
                "lost_item": item_to_dict(m.lost_item, "lost"),
                "candidate_item": item_to_dict(m.found_item, "found"),
                "match_score": m.match_score,
                "confidence": m.confidence_level,
                "factors": m.factor_breakdown,
                "reasons": m.reasons or [],
                "status": m.status,
                "created_at": m.created_at
            }
            for m in matches
        ]
    else:
        item = db.query(FoundItem).filter(FoundItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Found item not found")
        if item.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Forbidden")

        matches = (
            db.query(Match)
            .filter(Match.found_item_id == item_id)
            .order_by(desc(Match.match_score))
            .all()
        )
        return [
            {
                "match_id": m.id,
                "lost_item": item_to_dict(m.lost_item, "lost"),
                "candidate_item": item_to_dict(m.lost_item, "lost"),
                "match_score": m.match_score,
                "confidence": m.confidence_level,
                "factors": m.factor_breakdown,
                "reasons": m.reasons or [],
                "status": m.status,
                "created_at": m.created_at
            }
            for m in matches
        ]


@router.get("/match/{match_id}")
@router.get("/matching/{match_id}")
def get_match_by_id(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves match details by match ID.
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with ID {match_id} not found."
        )

    is_claimant = match.lost_item.user_id == current_user.id if match.lost_item else False
    is_finder = match.found_item.user_id == current_user.id if match.found_item else False
    if not (is_claimant or is_finder or current_user.role == "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this match."
        )

    return {
        "match_id": match.id,
        "lost_item": item_to_dict(match.lost_item, "lost") if match.lost_item else None,
        "candidate_item": item_to_dict(match.found_item, "found") if match.found_item else None,
        "match_score": match.match_score,
        "confidence": match.confidence_level,
        "factors": match.factor_breakdown,
        "reasons": match.reasons or [],
        "status": match.status,
        "created_at": match.created_at
    }


# -----------------------------------------------------------------------------
# Direct Attribute Extraction Test Endpoint
# -----------------------------------------------------------------------------
@router.post("/extract")
def extract_attributes_endpoint(
    payload: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Direct endpoint for testing the Information Extraction Agent on raw item descriptions.
    """
    title = payload.get("title", "")
    description = payload.get("description", "")
    category = payload.get("category")
    color = payload.get("color")
    brand = payload.get("brand")
    model = payload.get("model")
    location = payload.get("location")
    distinctive_features = payload.get("distinctive_features")

    result = extract_item_attributes(
        title=title,
        description=description,
        category=category,
        color=color,
        brand=brand,
        model=model,
        location=location,
        distinctive_features=distinctive_features
    )
    return result
