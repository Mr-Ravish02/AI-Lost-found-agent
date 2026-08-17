import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_

from app.database import get_db
from app.models.user import User
from app.models.item import LostItem, FoundItem, Match, VerificationQuestion, VerificationAnswer, AdminAction
from app.schemas.admin import (
    AdminStatsResponse,
    AdminActionRequest,
    AdminMatchSummary,
    AdminMatchDetailResponse
)
from app.agents.matching_agent import item_to_dict
from app.routers.auth import get_current_user
from app.routers.notifications import create_user_notification

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard & Decision Hub"])


def require_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency ensuring only users with admin role can access endpoints."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Operation requires administrator privileges."
        )
    return current_user


# -----------------------------------------------------------------------------
# Admin Dashboard Statistics
# -----------------------------------------------------------------------------
@router.get("/dashboard/stats", response_model=AdminStatsResponse)
def get_admin_dashboard_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin_user)
):
    """
    Returns high-level statistics for the Admin Dashboard:
    Total Lost Items, Total Found Items, Potential Matches, Pending Reviews, Resolved Cases.
    """
    total_lost = db.query(LostItem).count()
    total_found = db.query(FoundItem).count()
    potential_matches = db.query(Match).count()
    
    # Pending reviews are matches currently in admin_review or verification/in_progress
    pending_reviews = (
        db.query(Match)
        .filter(Match.status.in_(["pending", "admin_review", "in_progress", "verification_pending", "submitted", "evaluated"]))
        .count()
    )
    
    # Resolved cases are approved matches or returned items
    resolved_matches = db.query(Match).filter(Match.status == "approved").count()
    resolved_lost = db.query(LostItem).filter(LostItem.status.in_(["returned", "matched"])).count()
    resolved_cases = max(resolved_matches, resolved_lost)

    return AdminStatsResponse(
        total_lost=total_lost,
        total_found=total_found,
        potential_matches=potential_matches,
        pending_reviews=pending_reviews,
        resolved_cases=resolved_cases
    )


# -----------------------------------------------------------------------------
# Get Pending Matches for Admin Review
# -----------------------------------------------------------------------------
@router.get("/matches/pending", response_model=List[AdminMatchSummary])
def get_pending_matches(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin_user)
):
    """
    Retrieves all matches awaiting administrator evaluation or in verification review.
    """
    matches = (
        db.query(Match)
        .filter(Match.status.in_(["pending", "admin_review", "in_progress", "verification_pending", "submitted", "evaluated", "suggested"]))
        .order_by(desc(Match.match_score))
        .all()
    )

    results = []
    for m in matches:
        # Get latest verification answers score if any
        answers = (
            db.query(VerificationAnswer)
            .join(VerificationQuestion)
            .filter(VerificationQuestion.match_id == m.id)
            .all()
        )
        v_score = None
        v_eval = None
        if answers:
            scores = [a.evaluation_score for a in answers if a.evaluation_score is not None]
            if scores:
                v_score = round(sum(scores) / len(scores), 1)
            v_eval = answers[0].evaluation_feedback

        results.append(
            AdminMatchSummary(
                match_id=m.id,
                lost_item=item_to_dict(m.lost_item, "lost") if m.lost_item else {},
                found_item=item_to_dict(m.found_item, "found") if m.found_item else {},
                match_score=m.match_score,
                confidence_level=m.confidence_level,
                factor_breakdown=m.factor_breakdown,
                reasons=m.reasons or [],
                status=m.status,
                verification_score=v_score,
                verification_evaluation=v_eval,
                answers_count=len(answers),
                created_at=m.created_at,
                updated_at=m.updated_at
            )
        )

    return results


# -----------------------------------------------------------------------------
# Get Detailed Match Information for Admin
# -----------------------------------------------------------------------------
@router.get("/matches/{match_id}", response_model=AdminMatchDetailResponse)
def get_admin_match_detail(
    match_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin_user)
):
    """
    Retrieves full details for a match:
    Lost item, Found item, factor breakdown, verification questions, claimant answers, and admin action audit log.
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with ID {match_id} not found."
        )

    # Fetch verification questions and answers
    questions = match.questions
    answers = (
        db.query(VerificationAnswer)
        .join(VerificationQuestion)
        .filter(VerificationQuestion.match_id == match.id)
        .order_by(VerificationAnswer.created_at.desc())
        .all()
    )

    v_score = None
    v_eval = None
    if answers:
        scores = [a.evaluation_score for a in answers if a.evaluation_score is not None]
        if scores:
            v_score = round(sum(scores) / len(scores), 1)
        v_eval = answers[0].evaluation_feedback

    # Admin actions audit log
    actions = (
        db.query(AdminAction)
        .filter(AdminAction.match_id == match.id)
        .order_by(desc(AdminAction.created_at))
        .all()
    )

    return AdminMatchDetailResponse(
        match_id=match.id,
        lost_item=item_to_dict(match.lost_item, "lost") if match.lost_item else {},
        found_item=item_to_dict(match.found_item, "found") if match.found_item else {},
        match_score=match.match_score,
        confidence_level=match.confidence_level,
        factor_breakdown=match.factor_breakdown,
        reasons=match.reasons or [],
        status=match.status,
        admin_notes=match.admin_notes,
        verification_score=v_score,
        verification_evaluation=v_eval,
        questions=[
            {
                "id": q.id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "created_at": str(q.created_at) if q.created_at else None
            }
            for q in questions
        ],
        answers=[
            {
                "id": a.id,
                "question_id": a.question_id,
                "user_id": a.user_id,
                "answer_text": a.answer_text,
                "evaluation_score": a.evaluation_score,
                "evaluation_feedback": a.evaluation_feedback,
                "created_at": str(a.created_at) if a.created_at else None
            }
            for a in answers
        ],
        admin_actions=[
            {
                "id": act.id,
                "admin_id": act.admin_id,
                "action": act.action,
                "reason": act.reason,
                "created_at": str(act.created_at) if act.created_at else None
            }
            for act in actions
        ],
        created_at=match.created_at,
        updated_at=match.updated_at
    )


# -----------------------------------------------------------------------------
# Decision: Approve Match
# -----------------------------------------------------------------------------
@router.post("/matches/{match_id}/approve")
def approve_match(
    match_id: int,
    payload: AdminActionRequest = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin_user)
):
    """
    Administrator approves ownership match.
    Updates match to 'approved', resolves lost & found item statuses to 'returned',
    logs admin audit action, and sends user notifications.
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with ID {match_id} not found."
        )

    notes = payload.notes or payload.reason if payload else "Approved by administrator"

    # Update match
    match.status = "approved"
    match.admin_notes = notes

    # Update item statuses to returned/matched
    if match.lost_item:
        match.lost_item.status = "returned"
    if match.found_item:
        match.found_item.status = "returned"

    # Record Admin Action
    action = AdminAction(
        match_id=match.id,
        admin_id=admin_user.id,
        action="approved",
        reason=notes
    )
    db.add(action)
    db.commit()
    db.refresh(match)

    # Send Notification to claimant
    if match.lost_item:
        create_user_notification(
            user_id=match.lost_item.user_id,
            title="🎉 Match Approved!",
            message="Your lost item match has been approved. Please visit the help desk to collect your item.",
            notification_type="admin_update",
            link=f"/dashboard",
            db=db
        )

    # Send Notification to finder
    if match.found_item:
        create_user_notification(
            user_id=match.found_item.user_id,
            title="✅ Item Claim Completed",
            message="The item you found has been successfully verified and returned to its owner. Thank you!",
            notification_type="admin_update",
            link=f"/dashboard",
            db=db
        )

    return {
        "message": "Match successfully approved.",
        "match_id": match.id,
        "status": match.status,
        "admin_notes": match.admin_notes
    }


# -----------------------------------------------------------------------------
# Decision: Reject Match
# -----------------------------------------------------------------------------
@router.post("/matches/{match_id}/reject")
def reject_match(
    match_id: int,
    payload: AdminActionRequest = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin_user)
):
    """
    Administrator rejects match.
    Updates match to 'rejected', logs admin audit action, and notifies claimant.
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with ID {match_id} not found."
        )

    notes = payload.notes or payload.reason if payload else "Rejected by administrator"

    match.status = "rejected"
    match.admin_notes = notes

    # If lost item was marked matched, re-activate it for further searching
    if match.lost_item and match.lost_item.status == "matched":
        match.lost_item.status = "active"
    if match.found_item and match.found_item.status == "matched":
        match.found_item.status = "active"

    action = AdminAction(
        match_id=match.id,
        admin_id=admin_user.id,
        action="rejected",
        reason=notes
    )
    db.add(action)
    db.commit()
    db.refresh(match)

    # Send Notification to claimant
    if match.lost_item:
        create_user_notification(
            user_id=match.lost_item.user_id,
            title="❌ Match Not Approved",
            message="The match was not approved based on verification analysis. Your item remains active for new matches.",
            notification_type="admin_update",
            link=f"/dashboard",
            db=db
        )

    return {
        "message": "Match has been rejected.",
        "match_id": match.id,
        "status": match.status,
        "admin_notes": match.admin_notes
    }


# -----------------------------------------------------------------------------
# Decision: Request More Information
# -----------------------------------------------------------------------------
@router.post("/matches/{match_id}/request-info")
def request_more_info(
    match_id: int,
    payload: AdminActionRequest = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin_user)
):
    """
    Administrator requests further proof / additional verification details.
    Transitions match status back to in_progress and notifies claimant.
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with ID {match_id} not found."
        )

    notes = payload.notes or payload.reason if payload else "Additional information requested by administrator"

    match.status = "in_progress"
    match.admin_notes = notes

    action = AdminAction(
        match_id=match.id,
        admin_id=admin_user.id,
        action="requested_more_info",
        reason=notes
    )
    db.add(action)
    db.commit()
    db.refresh(match)

    # Send Notification to claimant
    if match.lost_item:
        create_user_notification(
            user_id=match.lost_item.user_id,
            title="ℹ️ Additional Verification Needed",
            message=f"Administrator requested additional details: {notes}",
            notification_type="verification_needed",
            link=f"/dashboard",
            db=db
        )

    return {
        "message": "Additional verification requested.",
        "match_id": match.id,
        "status": match.status,
        "admin_notes": match.admin_notes
    }
