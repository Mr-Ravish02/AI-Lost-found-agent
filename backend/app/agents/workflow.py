import logging
from typing import Dict, Any, List, Optional, TypedDict
from sqlalchemy.orm import Session

from langgraph.graph import StateGraph, START, END

from app.database import SessionLocal
from app.models.item import LostItem, FoundItem, Match, VerificationQuestion, VerificationAnswer
from app.agents.extraction_agent import extract_item_attributes
from app.agents.matching_agent import find_matches_for_lost_item, item_to_dict
from app.agents.verification_agent import (
    generate_verification_questions,
    evaluate_verification_answers,
    evaluate_single_answer
)
from app.schemas.verification import VerificationAnswerIn

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Shared Workflow State
# -----------------------------------------------------------------------------
class WorkflowState(TypedDict, total=False):
    item_id: int
    item_type: str  # "lost" or "found"
    extracted_information: Optional[Dict[str, Any]]
    candidate_matches: List[Dict[str, Any]]
    selected_match: Optional[Dict[str, Any]]
    match_id: Optional[int]
    match_score: float
    match_confidence: str  # "none", "low", "medium", "high"
    verification_questions: List[Dict[str, Any]]
    verification_answers: List[Dict[str, Any]]
    verification_score: Optional[float]
    verification_evaluation: Optional[str]
    recommendation: str
    current_status: str
    admin_review_payload: Optional[Dict[str, Any]]
    errors: List[str]
    db: Any


# -----------------------------------------------------------------------------
# Node 1: Information Extraction Agent Node
# -----------------------------------------------------------------------------
def extraction_node(state: WorkflowState) -> WorkflowState:
    """
    Extracts and standardizes item metadata from raw user input.
    Enriches item attributes in state and database if needed.
    """
    errors = list(state.get("errors", []))
    item_id = state.get("item_id")
    item_type = state.get("item_type", "lost")
    db: Optional[Session] = state.get("db")

    extracted_info = None

    if db and item_id:
        try:
            if item_type == "lost":
                item = db.query(LostItem).filter(LostItem.id == item_id).first()
            else:
                item = db.query(FoundItem).filter(FoundItem.id == item_id).first()

            if item:
                # Run extraction agent to ensure normalized structured data
                extracted = extract_item_attributes(
                    title=item.title,
                    description=item.description,
                    category=item.category,
                    color=item.color,
                    brand=item.brand,
                    model=item.model,
                    location=item.location,
                    distinctive_features=item.distinctive_features
                )
                
                # Update item record with any newly discovered tags
                item.extracted_tags = extracted
                if not item.distinctive_features and extracted.get("distinctive_features"):
                    item.distinctive_features = extracted["distinctive_features"]
                db.commit()
                db.refresh(item)

                extracted_info = {
                    "id": item.id,
                    "title": item.title,
                    "category": item.category,
                    "color": item.color,
                    "brand": item.brand,
                    "model": item.model,
                    "location": item.location,
                    "distinctive_features": item.distinctive_features,
                    "extracted_tags": extracted
                }
            else:
                errors.append(f"Item with ID {item_id} not found in database.")
        except Exception as exc:
            logger.error(f"Error in extraction_node: {exc}", exc_info=True)
            errors.append(f"Extraction error: {str(exc)}")

    return {
        **state,
        "extracted_information": extracted_info,
        "current_status": "extracted",
        "errors": errors
    }


# -----------------------------------------------------------------------------
# Node 2: Matching Agent Node
# -----------------------------------------------------------------------------
def matching_node(state: WorkflowState) -> WorkflowState:
    """
    Executes the Multi-Factor AI Matching Agent against candidate found items in the database.
    Ranks potential matches and stores results in state.
    """
    errors = list(state.get("errors", []))
    item_id = state.get("item_id")
    db: Optional[Session] = state.get("db")

    candidates: List[Dict[str, Any]] = []
    top_match: Optional[Dict[str, Any]] = None
    match_id = None
    match_score = 0.0
    match_confidence = "none"

    if db and item_id:
        try:
            match_res = find_matches_for_lost_item(item_id, db, min_score_threshold=35.0)
            candidates = match_res.get("matches", [])
            if candidates:
                top_match = candidates[0]
                match_id = top_match.get("match_id")
                match_score = top_match.get("match_score", 0.0)
                match_confidence = top_match.get("confidence", "low")
        except Exception as exc:
            logger.error(f"Error in matching_node: {exc}", exc_info=True)
            errors.append(f"Matching error: {str(exc)}")

    return {
        **state,
        "candidate_matches": candidates,
        "selected_match": top_match,
        "match_id": match_id,
        "match_score": match_score,
        "match_confidence": match_confidence,
        "current_status": "matched",
        "errors": errors
    }


# -----------------------------------------------------------------------------
# Node 3: Evaluate Match Confidence Node
# -----------------------------------------------------------------------------
def confidence_node(state: WorkflowState) -> WorkflowState:
    """
    Evaluates similarity score and confidence level to determine routing:
    - none/low -> end with no_match / suggested status
    - medium -> route to verification and administrator review
    - high -> route to verification and administrator review
    """
    top_match = state.get("selected_match")
    confidence = state.get("match_confidence", "none")
    score = state.get("match_score", 0.0)

    if not top_match or confidence in ["none", "low"]:
        status = "no_match" if not top_match else "suggested"
        recommendation = "keep_searching"
    elif confidence == "medium":
        status = "in_progress"
        recommendation = "verification_needed"
    else:  # high
        status = "in_progress"
        recommendation = "generate_verification_questions"

    return {
        **state,
        "current_status": status,
        "recommendation": recommendation
    }


# -----------------------------------------------------------------------------
# Node 4: Verification Generation Agent Node
# -----------------------------------------------------------------------------
def verification_generation_node(state: WorkflowState) -> WorkflowState:
    """
    Invokes the Verification Agent to generate 3-5 privacy-preserving ownership questions.
    Ensures zero leakage of secret found-item details.
    """
    errors = list(state.get("errors", []))
    match_id = state.get("match_id")
    db: Optional[Session] = state.get("db")

    questions_out: List[Dict[str, Any]] = []

    if db and match_id:
        try:
            match_obj = db.query(Match).filter(Match.id == match_id).first()
            if match_obj:
                db_questions = generate_verification_questions(match_obj, db)
                questions_out = [
                    {
                        "id": q.id,
                        "match_id": q.match_id,
                        "question": q.question_text,
                        "question_text": q.question_text,
                        "question_type": q.question_type
                    }
                    for q in db_questions
                ]
            else:
                errors.append(f"Match ID {match_id} not found in database.")
        except Exception as exc:
            logger.error(f"Error in verification_generation_node: {exc}", exc_info=True)
            errors.append(f"Verification question generation error: {str(exc)}")

    return {
        **state,
        "verification_questions": questions_out,
        "current_status": "in_progress",
        "recommendation": "awaiting_claimant_verification",
        "errors": errors
    }


# -----------------------------------------------------------------------------
# Node 5: Verification Evaluation Agent Node
# -----------------------------------------------------------------------------
def verification_evaluation_node(state: WorkflowState) -> WorkflowState:
    """
    Evaluates submitted claimant answers against ground truth lost/found reports.
    Computes scores, confidence, and feedback reasons.
    """
    errors = list(state.get("errors", []))
    match_id = state.get("match_id")
    db: Optional[Session] = state.get("db")
    answers_in = state.get("verification_answers", [])

    verification_score = 0.0
    evaluation_feedback = "No answers submitted"
    evaluated_answers = []

    if db and match_id and answers_in:
        try:
            match_obj = db.query(Match).filter(Match.id == match_id).first()
            if match_obj:
                user_id = match_obj.lost_item.user_id if match_obj.lost_item else 1
                
                # Format answers for evaluation
                formatted_in = [
                    VerificationAnswerIn(
                        question_id=a["question_id"],
                        answer_text=a.get("answer_text") or a.get("answer", "")
                    )
                    for a in answers_in
                    if "question_id" in a
                ]

                eval_result = evaluate_verification_answers(
                    match=match_obj,
                    answers_in=formatted_in,
                    user_id=user_id,
                    db=db
                )

                verification_score = eval_result["verification_score"]
                evaluation_feedback = "; ".join(eval_result.get("reasons", []))
                evaluated_answers = [
                    {
                        "id": a.id,
                        "question_id": a.question_id,
                        "answer_text": a.answer_text,
                        "evaluation_score": a.evaluation_score,
                        "evaluation_feedback": a.evaluation_feedback
                    }
                    for a in eval_result["answers"]
                ]
        except Exception as exc:
            logger.error(f"Error in verification_evaluation_node: {exc}", exc_info=True)
            errors.append(f"Verification evaluation error: {str(exc)}")

    return {
        **state,
        "verification_answers": evaluated_answers if evaluated_answers else answers_in,
        "verification_score": verification_score,
        "verification_evaluation": evaluation_feedback,
        "current_status": "evaluated",
        "errors": errors
    }


# -----------------------------------------------------------------------------
# Node 6: Admin Review Node (Human-in-the-Loop)
# -----------------------------------------------------------------------------
def admin_review_node(state: WorkflowState) -> WorkflowState:
    """
    Prepares the complete administrative dossier and transitions the match status to admin_review.
    NEVER automatically approves ownership — Final approval rests with human administrator.
    """
    errors = list(state.get("errors", []))
    match_id = state.get("match_id")
    db: Optional[Session] = state.get("db")

    admin_payload = None

    if db and match_id:
        try:
            match_obj = db.query(Match).filter(Match.id == match_id).first()
            if match_obj:
                match_obj.status = "admin_review"
                db.commit()
                db.refresh(match_obj)

                lost_dict = item_to_dict(match_obj.lost_item, "lost") if match_obj.lost_item else {}
                found_dict = item_to_dict(match_obj.found_item, "found") if match_obj.found_item else {}

                admin_payload = {
                    "match_id": match_obj.id,
                    "lost_item": lost_dict,
                    "found_item": found_dict,
                    "match_score": match_obj.match_score,
                    "confidence_level": match_obj.confidence_level,
                    "factor_breakdown": match_obj.factor_breakdown,
                    "matching_reasons": match_obj.reasons or [],
                    "verification_score": state.get("verification_score"),
                    "verification_evaluation": state.get("verification_evaluation"),
                    "answers": state.get("verification_answers", []),
                    "available_actions": ["APPROVE", "REJECT", "REQUEST_MORE_INFO"]
                }
        except Exception as exc:
            logger.error(f"Error in admin_review_node: {exc}", exc_info=True)
            errors.append(f"Admin review compilation error: {str(exc)}")

    return {
        **state,
        "admin_review_payload": admin_payload,
        "current_status": "admin_review",
        "recommendation": "administrator_review",
        "errors": errors
    }


# -----------------------------------------------------------------------------
# Conditional Routing Functions
# -----------------------------------------------------------------------------
def route_on_confidence(state: WorkflowState) -> str:
    """
    Routes from confidence_node:
    - medium or high confidence -> verification_generation_node
    - low or none -> END
    """
    confidence = state.get("match_confidence", "none")
    selected_match = state.get("selected_match")
    if selected_match and confidence in ["medium", "high"]:
        return "verification_generation_node"
    return END


def route_on_answers(state: WorkflowState) -> str:
    """
    Routes from verification_generation_node:
    - if answers provided in state -> verification_evaluation_node
    - otherwise (awaiting user verification submission) -> END
    """
    answers = state.get("verification_answers")
    if answers and len(answers) > 0:
        return "verification_evaluation_node"
    return END


# -----------------------------------------------------------------------------
# LangGraph Workflow Construction
# -----------------------------------------------------------------------------
def build_agentic_workflow():
    """
    Constructs the compiled LangGraph StateGraph workflow connecting:
    Extraction -> Matching -> Confidence -> Verification Gen -> Verification Eval -> Admin Review
    """
    workflow = StateGraph(WorkflowState)

    # Add Nodes
    workflow.add_node("extraction_node", extraction_node)
    workflow.add_node("matching_node", matching_node)
    workflow.add_node("confidence_node", confidence_node)
    workflow.add_node("verification_generation_node", verification_generation_node)
    workflow.add_node("verification_evaluation_node", verification_evaluation_node)
    workflow.add_node("admin_review_node", admin_review_node)

    # Add Edges
    workflow.add_edge(START, "extraction_node")
    workflow.add_edge("extraction_node", "matching_node")
    workflow.add_edge("matching_node", "confidence_node")

    # Conditional edge on match confidence
    workflow.add_conditional_edges(
        "confidence_node",
        route_on_confidence,
        {
            "verification_generation_node": "verification_generation_node",
            END: END
        }
    )

    # Conditional edge on answer availability
    workflow.add_conditional_edges(
        "verification_generation_node",
        route_on_answers,
        {
            "verification_evaluation_node": "verification_evaluation_node",
            END: END
        }
    )

    workflow.add_edge("verification_evaluation_node", "admin_review_node")
    workflow.add_edge("admin_review_node", END)

    return workflow.compile()


# Global compiled workflow instance
compiled_lost_found_workflow = build_agentic_workflow()


# -----------------------------------------------------------------------------
# High-Level Execution Helper
# -----------------------------------------------------------------------------
def run_lost_item_workflow(
    lost_item_id: int,
    db: Session,
    answers: Optional[List[Dict[str, Any]]] = None
) -> WorkflowState:
    """
    Executes the full LangGraph agentic workflow for a lost item report.
    Handles graceful fallbacks and returns structured workflow state.
    """
    initial_state: WorkflowState = {
        "item_id": lost_item_id,
        "item_type": "lost",
        "extracted_information": None,
        "candidate_matches": [],
        "selected_match": None,
        "match_id": None,
        "match_score": 0.0,
        "match_confidence": "none",
        "verification_questions": [],
        "verification_answers": answers or [],
        "verification_score": None,
        "verification_evaluation": None,
        "recommendation": "initializing",
        "current_status": "pending",
        "admin_review_payload": None,
        "errors": [],
        "db": db
    }

    try:
        final_state = compiled_lost_found_workflow.invoke(initial_state)
        return final_state
    except Exception as exc:
        logger.error(f"LangGraph execution exception: {exc}", exc_info=True)
        return {
            **initial_state,
            "current_status": "error",
            "errors": [str(exc)]
        }
