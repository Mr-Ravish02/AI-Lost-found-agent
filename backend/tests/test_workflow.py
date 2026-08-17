import pytest
from app.models.item import LostItem, FoundItem, Match, VerificationQuestion
from app.agents.workflow import run_lost_item_workflow, compiled_lost_found_workflow


def test_workflow_no_candidates(db, claimant_user):
    """Path 1: Lost item with zero candidate found items in DB."""
    lost = LostItem(
        user_id=claimant_user["user"].id,
        title="Red Backpack",
        category="Wallets & Bags",
        description="Red Jansport backpack left in cafeteria.",
        color="Red",
        brand="Jansport",
        location="Cafeteria",
        date_lost="2026-03-01",
        status="active"
    )
    db.add(lost)
    db.commit()
    db.refresh(lost)

    final_state = run_lost_item_workflow(lost.id, db)

    assert final_state["item_id"] == lost.id
    assert final_state["match_confidence"] == "none"
    assert final_state["current_status"] in ["no_match", "pending"]
    assert final_state["recommendation"] == "keep_searching"
    assert len(final_state["verification_questions"]) == 0


def test_workflow_low_confidence_path(db, claimant_user, finder_user):
    """Path 2: Low-confidence match (<50% or distant category) routes to END without verification."""
    lost = LostItem(
        user_id=claimant_user["user"].id,
        title="Black Umbrella",
        category="Accessories & Jewelry",
        description="Black umbrella left in bus stop.",
        color="Black",
        location="Bus Stop",
        date_lost="2026-03-01",
        status="active"
    )
    db.add(lost)

    found = FoundItem(
        user_id=finder_user["user"].id,
        title="Silver Ring",
        category="Accessories & Jewelry",
        description="Silver ring with small stone found in library.",
        color="Silver",
        location="Library",
        date_found="2026-03-01",
        status="active"
    )
    db.add(found)
    db.commit()

    final_state = run_lost_item_workflow(lost.id, db)

    assert final_state["item_id"] == lost.id
    # Low confidence should NOT generate verification questions
    assert len(final_state["verification_questions"]) == 0
    assert final_state["match_confidence"] in ["low", "none"]


def test_workflow_high_confidence_path_generates_questions(db, claimant_user, finder_user):
    """Path 3: High-confidence match routes to verification question generator."""
    lost = LostItem(
        user_id=claimant_user["user"].id,
        title="Black Dell XPS Laptop",
        category="Electronics",
        description="Black Dell XPS 15 laptop with red sticker lost near library 2nd floor.",
        color="Black",
        brand="Dell",
        model="XPS 15",
        location="Library 2nd floor",
        date_lost="2026-03-01",
        distinctive_features=["red sticker on lid"],
        status="active"
    )
    db.add(lost)

    found = FoundItem(
        user_id=finder_user["user"].id,
        title="Found Dell Laptop",
        category="Electronics",
        description="Black Dell XPS laptop found on table in library with red sticker.",
        color="Black",
        brand="Dell",
        model="XPS",
        location="Main Library",
        date_found="2026-03-01",
        distinctive_features=["red sticker on lid"],
        status="active"
    )
    db.add(found)
    db.commit()

    final_state = run_lost_item_workflow(lost.id, db)

    assert final_state["item_id"] == lost.id
    assert final_state["match_confidence"] in ["high", "medium"]
    assert final_state["match_score"] >= 60.0
    assert len(final_state["verification_questions"]) >= 3
    assert final_state["current_status"] == "in_progress"

    # Ensure DB questions created
    db_q = db.query(VerificationQuestion).filter(VerificationQuestion.match_id == final_state["match_id"]).all()
    assert len(db_q) == len(final_state["verification_questions"])


def test_workflow_full_cycle_with_answers_to_admin_review(db, claimant_user, finder_user):
    """Path 4: Workflow with answers evaluated routes through to admin_review (Never auto-approved)."""
    lost = LostItem(
        user_id=claimant_user["user"].id,
        title="Navy Blue Sony Headphones",
        category="Electronics",
        description="Navy blue Sony WH-1000XM5 wireless headphones lost in study room 3.",
        color="Navy Blue",
        brand="Sony",
        model="WH-1000XM5",
        location="Study Room 3",
        date_lost="2026-03-04",
        status="active"
    )
    db.add(lost)

    found = FoundItem(
        user_id=finder_user["user"].id,
        title="Found Sony Wireless Headphones",
        category="Electronics",
        description="Navy blue Sony headphones found in study lounge.",
        color="Navy Blue",
        brand="Sony",
        model="WH-1000XM5",
        location="Study Lounge",
        date_found="2026-03-04",
        status="active"
    )
    db.add(found)
    db.commit()

    # 1. First run generates questions
    gen_state = run_lost_item_workflow(lost.id, db)
    questions = gen_state["verification_questions"]
    assert len(questions) >= 3

    # 2. Provide claimant answers
    answers = [
        {"question_id": q["id"], "answer_text": "Sony WH-1000XM5 navy blue headphones lost near study room on March 4th"}
        for q in questions
    ]

    # 3. Second run with answers executes evaluation -> admin_review
    eval_state = run_lost_item_workflow(lost.id, db, answers=answers)

    assert eval_state["current_status"] == "admin_review"
    assert eval_state["recommendation"] == "administrator_review"
    assert eval_state["verification_score"] is not None
    assert eval_state["verification_score"] >= 60.0

    # Ensure admin review dossier is prepared
    admin_payload = eval_state["admin_review_payload"]
    assert admin_payload is not None
    assert admin_payload["match_id"] == eval_state["match_id"]
    assert "available_actions" in admin_payload
    assert "APPROVE" in admin_payload["available_actions"]

    # Critical: Status MUST NOT be automatically approved
    assert eval_state["current_status"] != "approved"
    db_match = db.query(Match).filter(Match.id == eval_state["match_id"]).first()
    assert db_match.status == "admin_review"


def test_workflow_api_trigger_as_claimant(client, claimant_user, sample_match):
    lost = sample_match["lost"]
    response = client.post(
        f"/api/ai/workflow/lost/{lost.id}",
        headers=claimant_user["headers"]
    )
    assert response.status_code == 200
    data = response.json()
    assert data["item_id"] == lost.id
    assert data["workflow_status"] == "in_progress"
    assert data["match_candidates_count"] >= 1
    assert data["match_score"] >= 60.0
    assert len(data["verification_questions"]) >= 3


def test_workflow_api_trigger_as_admin(client, admin_user, sample_match):
    lost = sample_match["lost"]
    response = client.post(
        f"/api/ai/workflow/lost/{lost.id}",
        headers=admin_user["headers"]
    )
    assert response.status_code == 200
    data = response.json()
    assert data["item_id"] == lost.id
    assert data["workflow_status"] == "in_progress"
    assert len(data["verification_questions"]) >= 3


def test_workflow_api_forbidden_for_stranger(client, stranger_user, sample_match):
    lost = sample_match["lost"]
    response = client.post(
        f"/api/ai/workflow/lost/{lost.id}",
        headers=stranger_user["headers"]
    )
    assert response.status_code == 403


def test_workflow_api_not_found(client, claimant_user):
    response = client.post(
        "/api/ai/workflow/lost/99999",
        headers=claimant_user["headers"]
    )
    assert response.status_code == 404


def test_workflow_api_verify_submits_to_admin_review(client, claimant_user, sample_match):
    lost = sample_match["lost"]

    # 1. Trigger workflow to get questions
    init_resp = client.post(
        f"/api/ai/workflow/lost/{lost.id}",
        headers=claimant_user["headers"]
    )
    assert init_resp.status_code == 200
    questions = init_resp.json()["verification_questions"]

    # 2. Submit verification answers
    answers_payload = [
        {"question_id": q["id"], "answer_text": "Dell XPS 15 laptop black color"}
        for q in questions
    ]

    verify_resp = client.post(
        f"/api/ai/workflow/lost/{lost.id}/verify",
        headers=claimant_user["headers"],
        json={"answers": answers_payload}
    )
    assert verify_resp.status_code == 200
    data = verify_resp.json()
    assert data["workflow_status"] == "admin_review"
    assert data["recommendation"] == "administrator_review"
    assert data["verification_score"] is not None
