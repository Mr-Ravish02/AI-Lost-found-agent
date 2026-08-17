import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.item import LostItem, Match
from app.schemas.workflow import WorkflowResponse, WorkflowVerificationSubmission
from app.agents.workflow import run_lost_item_workflow
from app.routers.auth import get_current_user
from app.routers.notifications import create_user_notification

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai/workflow", tags=["Agentic Workflow (LangGraph)"])


def sanitize_match_for_claimant(match_data: Optional[Dict[str, Any]], is_admin: bool) -> Optional[Dict[str, Any]]:
    """
    Sanitizes candidate match data to ensure private/secret fields from found item are not leaked to claimant.
    """
    if not match_data:
        return None
    if is_admin:
        return match_data

    candidate = match_data.get("candidate_item", {})
    sanitized_candidate = {
        "id": candidate.get("id"),
        "type": candidate.get("type"),
        "title": candidate.get("title"),
        "category": candidate.get("category"),
        "color": candidate.get("color"),
        "location": candidate.get("location"),
        "date_found": candidate.get("date_found"),
        "status": candidate.get("status")
    }

    return {
        "match_id": match_data.get("match_id"),
        "lost_item": match_data.get("lost_item"),
        "candidate_item": sanitized_candidate,
        "match_score": match_data.get("match_score"),
        "confidence": match_data.get("confidence"),
        "reasons": match_data.get("reasons", []),
        "status": match_data.get("status")
    }


# -----------------------------------------------------------------------------
# Trigger LangGraph Workflow for a Lost Item
# -----------------------------------------------------------------------------
@router.post("/lost/{lost_item_id}", response_model=WorkflowResponse)
def trigger_workflow_for_lost_item(
    lost_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Executes the multi-agent LangGraph workflow:
    1. Information Extraction Agent (normalizes tags)
    2. Matching Agent (multi-factor similarity)
    3. Confidence Node (decision routing)
    4. Verification Agent (generates safe questions if medium/high confidence)
    """
    lost_item = db.query(LostItem).filter(LostItem.id == lost_item_id).first()
    if not lost_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lost item with ID {lost_item_id} not found."
        )

    # Permission check: claimant owner or administrator
    is_claimant = lost_item.user_id == current_user.id
    is_admin = current_user.role == "admin"
    if not (is_claimant or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not authorized to run workflow on this item."
        )

    try:
        final_state = run_lost_item_workflow(lost_item_id=lost_item_id, db=db)
        
        candidates = final_state.get("candidate_matches", [])
        top_match = final_state.get("selected_match")
        sanitized_top = sanitize_match_for_claimant(top_match, is_admin)

        if final_state.get("match_confidence") in ["medium", "high"]:
            create_user_notification(
                user_id=lost_item.user_id,
                title="🎯 Possible Match Found",
                message="🎯 A possible match has been found for your lost item.",
                notification_type="match_found",
                link="/dashboard",
                db=db
            )

        return WorkflowResponse(
            item_id=lost_item_id,
            workflow_status=final_state.get("current_status", "pending"),
            match_candidates_count=len(candidates),
            match_score=final_state.get("match_score", 0.0),
            confidence=final_state.get("match_confidence", "none"),
            recommendation=final_state.get("recommendation", "keep_searching"),
            best_match=sanitized_top,
            verification_status=final_state.get("current_status"),
            verification_questions=final_state.get("verification_questions", []),
            verification_score=final_state.get("verification_score"),
            verification_evaluation=final_state.get("verification_evaluation"),
            admin_review_payload=final_state.get("admin_review_payload") if is_admin else None,
            errors=final_state.get("errors", [])
        )
    except Exception as exc:
        logger.error(f"Workflow endpoint error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow failed: {str(exc)}"
        )


# -----------------------------------------------------------------------------
# Submit Verification Answers & Progress to Admin Review
# -----------------------------------------------------------------------------
@router.post("/lost/{lost_item_id}/verify", response_model=WorkflowResponse)
def submit_workflow_verification(
    lost_item_id: int,
    submission: WorkflowVerificationSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submits claimant answers into the LangGraph workflow:
    Evaluates answers -> Routes to Admin Review (Never auto-approved).
    """
    lost_item = db.query(LostItem).filter(LostItem.id == lost_item_id).first()
    if not lost_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lost item with ID {lost_item_id} not found."
        )

    is_claimant = lost_item.user_id == current_user.id
    is_admin = current_user.role == "admin"
    if not (is_claimant or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not authorized to submit verification for this item."
        )

    try:
        final_state = run_lost_item_workflow(
            lost_item_id=lost_item_id,
            db=db,
            answers=submission.answers
        )

        candidates = final_state.get("candidate_matches", [])
        top_match = final_state.get("selected_match")
        sanitized_top = sanitize_match_for_claimant(top_match, is_admin)

        create_user_notification(
            user_id=lost_item.user_id,
            title="📝 Verification Submitted",
            message="Your verification has been submitted for administrator review.",
            notification_type="admin_update",
            link="/dashboard",
            db=db
        )

        return WorkflowResponse(
            item_id=lost_item_id,
            workflow_status=final_state.get("current_status", "evaluated"),
            match_candidates_count=len(candidates),
            match_score=final_state.get("match_score", 0.0),
            confidence=final_state.get("match_confidence", "none"),
            recommendation=final_state.get("recommendation", "administrator_review"),
            best_match=sanitized_top,
            verification_status=final_state.get("current_status"),
            verification_questions=final_state.get("verification_questions", []),
            verification_score=final_state.get("verification_score"),
            verification_evaluation=final_state.get("verification_evaluation"),
            admin_review_payload=final_state.get("admin_review_payload") if is_admin else None,
            errors=final_state.get("errors", [])
        )
    except Exception as exc:
        logger.error(f"Workflow verification error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow verification failed: {str(exc)}"
        )
