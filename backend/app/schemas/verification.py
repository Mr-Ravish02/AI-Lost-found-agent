from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class VerificationQuestionOut(BaseModel):
    id: int
    match_id: int
    question: Optional[str] = None
    question_text: str
    question_type: Optional[str] = "general"
    created_at: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def sync_question_fields(cls, values: Any) -> Any:
        if hasattr(values, "__dict__"):
            # SQLAlchemy model instance
            q_text = getattr(values, "question_text", None) or getattr(values, "question", "")
            return {
                "id": getattr(values, "id", None),
                "match_id": getattr(values, "match_id", None),
                "question": q_text,
                "question_text": q_text,
                "question_type": getattr(values, "question_type", "general"),
                "created_at": getattr(values, "created_at", None),
            }
        elif isinstance(values, dict):
            q_text = values.get("question_text") or values.get("question") or ""
            values["question"] = q_text
            values["question_text"] = q_text
        return values

    class Config:
        from_attributes = True


class VerificationAnswerIn(BaseModel):
    question_id: int
    answer_text: Optional[str] = None
    answer: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def ensure_answer_text(cls, values: Any) -> Any:
        if isinstance(values, dict):
            text = values.get("answer_text") or values.get("answer")
            if not text or not str(text).strip():
                raise ValueError("Answer text cannot be empty.")
            values["answer_text"] = str(text).strip()
            values["answer"] = str(text).strip()
        return values


class VerificationAnswerSubmission(BaseModel):
    answers: List[VerificationAnswerIn] = Field(..., min_length=1)


class VerificationAnswerOut(BaseModel):
    id: int
    question_id: int
    user_id: int
    answer: Optional[str] = None
    answer_text: str
    score: Optional[float] = None
    evaluation_score: Optional[float] = None
    evaluation: Optional[str] = None
    evaluation_feedback: Optional[str] = None
    created_at: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def sync_answer_fields(cls, values: Any) -> Any:
        if hasattr(values, "__dict__"):
            ans = getattr(values, "answer_text", None) or getattr(values, "answer", "")
            sc = getattr(values, "evaluation_score", None) if getattr(values, "evaluation_score", None) is not None else getattr(values, "score", None)
            fb = getattr(values, "evaluation_feedback", None) or getattr(values, "evaluation", None)
            return {
                "id": getattr(values, "id", None),
                "question_id": getattr(values, "question_id", None),
                "user_id": getattr(values, "user_id", None),
                "answer": ans,
                "answer_text": ans,
                "score": sc,
                "evaluation_score": sc,
                "evaluation": fb,
                "evaluation_feedback": fb,
                "created_at": getattr(values, "created_at", None),
            }
        elif isinstance(values, dict):
            ans = values.get("answer_text") or values.get("answer") or ""
            values["answer"] = ans
            values["answer_text"] = ans
            sc = values.get("evaluation_score") if values.get("evaluation_score") is not None else values.get("score")
            values["score"] = sc
            values["evaluation_score"] = sc
            fb = values.get("evaluation_feedback") or values.get("evaluation")
            values["evaluation"] = fb
            values["evaluation_feedback"] = fb
        return values

    class Config:
        from_attributes = True


class VerificationEvaluationResponse(BaseModel):
    match_id: int
    verification_score: float
    confidence: str
    recommendation: str
    status: str
    reasons: List[str]
    answers: List[VerificationAnswerOut]


class VerificationDetailResponse(BaseModel):
    match_id: int
    match_status: str
    match_score: float
    confidence_level: str
    questions: List[VerificationQuestionOut]
    answers: List[VerificationAnswerOut]
    latest_evaluation_score: Optional[float] = None
    latest_evaluation_feedback: Optional[str] = None
