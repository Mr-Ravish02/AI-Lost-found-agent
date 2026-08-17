import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.item import LostItem, FoundItem, Match
from app.ai.similarity import calculate_match_similarity

logger = logging.getLogger(__name__)


def item_to_dict(item: Any, item_type: str) -> Dict[str, Any]:
    """Helper to standardize LostItem or FoundItem model instances into dictionary for similarity engine."""
    return {
        "id": item.id,
        "type": item_type,
        "title": item.title,
        "category": item.category,
        "description": item.description,
        "color": item.color,
        "brand": item.brand,
        "model": item.model,
        "location": item.location,
        "date_lost": getattr(item, "date_lost", None),
        "date_found": getattr(item, "date_found", None),
        "distinctive_features": item.distinctive_features,
        "image_url": item.image_url,
        "status": item.status,
        "created_at": str(item.created_at) if item.created_at else None,
        "user_name": item.user.full_name if getattr(item, "user", None) else None
    }


def find_matches_for_lost_item(
    lost_item_id: int, 
    db: Session, 
    min_score_threshold: float = 35.0
) -> Dict[str, Any]:
    """
    Matching Agent: Analyzes a specific lost item against active candidate found items in the database.
    Calculates multi-factor similarity, ranks results, and saves/updates top matches.
    """
    lost_item = db.query(LostItem).filter(LostItem.id == lost_item_id).first()
    if not lost_item:
        raise ValueError(f"Lost item with ID {lost_item_id} not found.")

    lost_dict = item_to_dict(lost_item, "lost")

    # Fetch candidate found items (exclude returned or cancelled items)
    candidate_found_items = (
        db.query(FoundItem)
        .filter(FoundItem.status.in_(["active", "matched"]))
        .all()
    )

    matches_result = []

    for found_item in candidate_found_items:
        found_dict = item_to_dict(found_item, "found")
        sim = calculate_match_similarity(lost_dict, found_dict)

        if sim["final_score"] >= min_score_threshold:
            # Save or update Match record in database
            db_match = (
                db.query(Match)
                .filter(
                    Match.lost_item_id == lost_item.id,
                    Match.found_item_id == found_item.id
                )
                .first()
            )

            if not db_match:
                db_match = Match(
                    lost_item_id=lost_item.id,
                    found_item_id=found_item.id,
                    match_score=sim["final_score"],
                    factor_breakdown=sim["factors"],
                    confidence_level=sim["confidence"],
                    reasons=sim["reasons"],
                    status="suggested"
                )
                db.add(db_match)
            else:
                db_match.match_score = sim["final_score"]
                db_match.factor_breakdown = sim["factors"]
                db_match.confidence_level = sim["confidence"]
                db_match.reasons = sim["reasons"]

            db.commit()
            db.refresh(db_match)

            matches_result.append({
                "match_id": db_match.id,
                "lost_item": lost_dict,
                "candidate_item": found_dict,
                "match_score": sim["final_score"],
                "confidence": sim["confidence"],
                "factors": sim["factors"],
                "reasons": sim["reasons"],
                "status": db_match.status
            })

    # Sort descending by match score
    matches_result.sort(key=lambda m: m["match_score"], reverse=True)

    return {
        "source_item": lost_dict,
        "total_candidates_analyzed": len(candidate_found_items),
        "matches_count": len(matches_result),
        "top_match": matches_result[0] if matches_result else None,
        "matches": matches_result
    }


def find_matches_for_found_item(
    found_item_id: int, 
    db: Session, 
    min_score_threshold: float = 35.0
) -> Dict[str, Any]:
    """
    Matching Agent: Analyzes a specific found item against active candidate lost items in the database.
    """
    found_item = db.query(FoundItem).filter(FoundItem.id == found_item_id).first()
    if not found_item:
        raise ValueError(f"Found item with ID {found_item_id} not found.")

    found_dict = item_to_dict(found_item, "found")

    candidate_lost_items = (
        db.query(LostItem)
        .filter(LostItem.status.in_(["active", "matched"]))
        .all()
    )

    matches_result = []

    for lost_item in candidate_lost_items:
        lost_dict = item_to_dict(lost_item, "lost")
        sim = calculate_match_similarity(lost_dict, found_dict)

        if sim["final_score"] >= min_score_threshold:
            db_match = (
                db.query(Match)
                .filter(
                    Match.lost_item_id == lost_item.id,
                    Match.found_item_id == found_item.id
                )
                .first()
            )

            if not db_match:
                db_match = Match(
                    lost_item_id=lost_item.id,
                    found_item_id=found_item.id,
                    match_score=sim["final_score"],
                    factor_breakdown=sim["factors"],
                    confidence_level=sim["confidence"],
                    reasons=sim["reasons"],
                    status="suggested"
                )
                db.add(db_match)
            else:
                db_match.match_score = sim["final_score"]
                db_match.factor_breakdown = sim["factors"]
                db_match.confidence_level = sim["confidence"]
                db_match.reasons = sim["reasons"]

            db.commit()
            db.refresh(db_match)

            matches_result.append({
                "match_id": db_match.id,
                "lost_item": lost_dict,
                "candidate_item": lost_dict,
                "match_score": sim["final_score"],
                "confidence": sim["confidence"],
                "factors": sim["factors"],
                "reasons": sim["reasons"],
                "status": db_match.status
            })

    matches_result.sort(key=lambda m: m["match_score"], reverse=True)

    return {
        "source_item": found_dict,
        "total_candidates_analyzed": len(candidate_lost_items),
        "matches_count": len(matches_result),
        "top_match": matches_result[0] if matches_result else None,
        "matches": matches_result
    }
