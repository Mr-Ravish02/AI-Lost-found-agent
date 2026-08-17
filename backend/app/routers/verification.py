import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.item import Match, VerificationQuestion, VerificationAnswer
from app.schemas.verification import (
    VerificationQuestionOut,
    VerificationAnswerSubmission,
    VerificationAnswerOut,
    VerificationEvaluationResponse,
    VerificationDetailResponse
)
from app.agents.verification_agent import (
    generate_verification_questions,
    evaluate_verification_answers
)
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai/verification", tags=["Ownership Verification Agent"])


def get_authorized_match(match_id: int, current_user: User, db: Session) -> Match:
    """Helper to verify match existence and access permissions (claimant and admin only)."""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with ID {match_id} not found."
        )

    # Permission check: strictly claimant owner or administrator
    is_claimant = match.lost_item.user_id == current_user.id if match.lost_item else False
    is_admin = current_user.role == "admin"

    if not (is_claimant or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only the authorized claimant and administrators can access verification information for this match."
        )

    return match


# -----------------------------------------------------------------------------
# Generate Verification Questions
# -----------------------------------------------------------------------------
@router.post("/{match_id}/generate", response_model=List[VerificationQuestionOut])
def generate_questions_for_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates privacy-preserving ownership verification questions for a potential match.
    Ensures ZERO private details from the found-item report are leaked to the claimant.
    """
    match = get_authorized_match(match_id, current_user, db)

    try:
        questions = generate_verification_questions(match, db)
        return questions
    except Exception as exc:
        logger.error(f"Verification question generation error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate verification questions: {str(exc)}"
        )


# -----------------------------------------------------------------------------
# Get Verification Details & Questions
# -----------------------------------------------------------------------------
@router.get("/{match_id}", response_model=VerificationDetailResponse)
def get_verification_details(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves verification questions, current match status, and submitted answers.
    Accessible only by the authorized claimant, finder, or administrators.
    """
    match = get_authorized_match(match_id, current_user, db)

    # Automatically generate questions if none exist yet
    questions = match.questions
    if not questions:
        questions = generate_verification_questions(match, db)

    # Fetch answers if any
    answers = (
        db.query(VerificationAnswer)
        .join(VerificationQuestion)
        .filter(VerificationQuestion.match_id == match.id)
        .order_by(VerificationAnswer.created_at.desc())
        .all()
    )

    latest_score = answers[0].evaluation_score if answers else None
    latest_feedback = answers[0].evaluation_feedback if answers else None

    return VerificationDetailResponse(
        match_id=match.id,
        match_status=match.status,
        match_score=match.match_score,
        confidence_level=match.confidence_level,
        questions=[
            VerificationQuestionOut(
                id=q.id,
                match_id=q.match_id,
                question_text=q.question_text,
                question_type=q.question_type,
                created_at=q.created_at
            )
            for q in questions
        ],
        answers=[
            VerificationAnswerOut(
                id=a.id,
                question_id=a.question_id,
                user_id=a.user_id,
                answer_text=a.answer_text,
                evaluation_score=a.evaluation_score,
                evaluation_feedback=a.evaluation_feedback,
                created_at=a.created_at
            )
            for a in answers
        ],
        latest_evaluation_score=latest_score,
        latest_evaluation_feedback=latest_feedback
    )


# -----------------------------------------------------------------------------
# Submit and Evaluate Verification Answers
# -----------------------------------------------------------------------------
@router.post("/{match_id}/answers", response_model=VerificationEvaluationResponse)
def submit_verification_answers(
    match_id: int,
    submission: VerificationAnswerSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submits claimant answers to verification questions.
    The Verification Agent evaluates the answers against ground truth facts.
    Transitions match status to 'admin_review' (Never auto-approves ownership).
    """
    match = get_authorized_match(match_id, current_user, db)

    # Only claimant or admin can submit answers
    is_claimant = match.lost_item.user_id == current_user.id if match.lost_item else False
    if not (is_claimant or current_user.role == "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the claimant owner can submit verification answers."
        )

    try:
        result = evaluate_verification_answers(
            match=match,
            answers_in=submission.answers,
            user_id=current_user.id,
            db=db
        )
        return VerificationEvaluationResponse(
            match_id=result["match_id"],
            verification_score=result["verification_score"],
            confidence=result["confidence"],
            recommendation=result["recommendation"],
            status=result["status"],
            reasons=result["reasons"],
            answers=[
                VerificationAnswerOut(
                    id=a.id,
                    question_id=a.question_id,
                    user_id=a.user_id,
                    answer_text=a.answer_text,
                    evaluation_score=a.evaluation_score,
                    evaluation_feedback=a.evaluation_feedback,
                    created_at=a.created_at
                )
                for a in result["answers"]
            ]
        )
    except Exception as exc:
        logger.error(f"Verification evaluation error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate verification answers: {str(exc)}"
        )
