import pytest
from app.models.item import VerificationQuestion, VerificationAnswer


def test_generate_verification_questions_api_as_claimant(client, claimant_user, sample_match):
    match = sample_match["match"]
    response = client.post(
        f"/api/ai/verification/{match.id}/generate",
        headers=claimant_user["headers"]
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert 3 <= len(data) <= 5
    for q in data:
        assert "id" in q
        assert "question_text" in q
        assert "question_type" in q
        assert "match_id" in q
        assert q["match_id"] == match.id


def test_generate_verification_questions_api_as_admin(client, admin_user, sample_match):
    match = sample_match["match"]
    response = client.post(
        f"/api/ai/verification/{match.id}/generate",
        headers=admin_user["headers"]
    )
    assert response.status_code == 200
    data = response.json()
    assert 3 <= len(data) <= 5


def test_verification_api_forbidden_for_unauthorized_user(client, stranger_user, sample_match):
    match = sample_match["match"]
    # Generate endpoint
    resp_gen = client.post(
        f"/api/ai/verification/{match.id}/generate",
        headers=stranger_user["headers"]
    )
    assert resp_gen.status_code == 403

    # Get endpoint
    resp_get = client.get(
        f"/api/ai/verification/{match.id}",
        headers=stranger_user["headers"]
    )
    assert resp_get.status_code == 403

    # Answers endpoint
    resp_ans = client.post(
        f"/api/ai/verification/{match.id}/answers",
        headers=stranger_user["headers"],
        json={"answers": [{"question_id": 1, "answer_text": "Random guess"}]}
    )
    assert resp_ans.status_code == 403


def test_verification_api_unauthenticated(client, sample_match):
    match = sample_match["match"]
    response = client.get(f"/api/ai/verification/{match.id}")
    assert response.status_code == 401


def test_get_verification_details_api(client, claimant_user, sample_match):
    match = sample_match["match"]
    response = client.get(
        f"/api/ai/verification/{match.id}",
        headers=claimant_user["headers"]
    )
    assert response.status_code == 200
    data = response.json()
    assert data["match_id"] == match.id
    assert "questions" in data
    assert 3 <= len(data["questions"]) <= 5
    assert data["match_status"] in ["in_progress", "pending", "suggested"]


def test_submit_verification_answers_api_evaluation(client, claimant_user, sample_match):
    match = sample_match["match"]
    
    # 1. Fetch / Generate questions
    get_resp = client.get(
        f"/api/ai/verification/{match.id}",
        headers=claimant_user["headers"]
    )
    assert get_resp.status_code == 200
    questions = get_resp.json()["questions"]

    # 2. Submit answers
    answers_payload = [
        {
            "question_id": q["id"],
            "answer_text": "Dell XPS 15 laptop with black finish and red sticker lost near library"
        }
        for q in questions
    ]

    submit_resp = client.post(
        f"/api/ai/verification/{match.id}/answers",
        headers=claimant_user["headers"],
        json={"answers": answers_payload}
    )
    assert submit_resp.status_code == 200
    eval_data = submit_resp.json()

    assert eval_data["match_id"] == match.id
    assert "verification_score" in eval_data
    assert eval_data["verification_score"] > 0
    assert eval_data["status"] == "admin_review"
    assert eval_data["recommendation"] == "administrator_review"
    assert len(eval_data["answers"]) == len(questions)

    # 3. Check subsequent GET reflects admin_review status and answers
    get_after = client.get(
        f"/api/ai/verification/{match.id}",
        headers=claimant_user["headers"]
    )
    assert get_after.status_code == 200
    after_data = get_after.json()
    assert after_data["match_status"] == "admin_review"
    assert len(after_data["answers"]) == len(questions)
    assert after_data["latest_evaluation_score"] is not None
