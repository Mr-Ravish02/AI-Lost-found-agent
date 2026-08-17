import pytest
from app.ai.similarity import calculate_match_similarity
from app.agents.matching_agent import find_matches_for_lost_item, find_matches_for_found_item
from app.models.item import LostItem, FoundItem, Match


def test_similarity_engine_high_match():
    lost = {
        "id": 1,
        "title": "Blue Dell Laptop",
        "category": "Electronics",
        "description": "Dell laptop with blue protective case and stickers lost in library.",
        "color": "Blue",
        "brand": "Dell",
        "location": "Library 2nd Floor",
        "date_lost": "2026-03-01",
        "distinctive_features": ["blue case", "stickers"]
    }
    found = {
        "id": 2,
        "title": "Found Blue Dell Laptop",
        "category": "Electronics",
        "description": "Dell laptop blue casing with stickers on top found in main library.",
        "color": "Blue",
        "brand": "Dell",
        "location": "Library",
        "date_found": "2026-03-01",
        "distinctive_features": ["blue casing", "stickers"]
    }

    result = calculate_match_similarity(lost, found)
    assert result["final_score"] >= 80.0
    assert result["confidence"] in ["high", "medium"]
    assert "factors" in result
    assert "reasons" in result


def test_similarity_engine_different_category():
    lost = {
        "id": 1,
        "title": "Black Wallet",
        "category": "Wallets & Purses",
        "description": "Leather wallet with cash and student ID.",
        "color": "Black",
        "brand": "Generic",
        "location": "Campus Center",
        "date_lost": "2026-03-01"
    }
    found = {
        "id": 2,
        "title": "Red Water Bottle",
        "category": "Bottles",
        "description": "Stainless steel red hydro flask.",
        "color": "Red",
        "brand": "Hydro Flask",
        "location": "Gym",
        "date_found": "2026-03-01"
    }

    result = calculate_match_similarity(lost, found)
    assert result["final_score"] < 40.0


def test_matching_agent_lost_and_found_flow(db, claimant_user, finder_user):
    lost = LostItem(
        user_id=claimant_user["user"].id,
        title="Silver MacBook Pro 14",
        category="Electronics",
        description="Apple MacBook Pro 14 inch M3 silver lost near computer lab.",
        color="Silver",
        brand="Apple",
        model="MacBook Pro 14",
        location="Engineering Lab",
        date_lost="2026-03-05",
        status="active"
    )
    db.add(lost)

    found = FoundItem(
        user_id=finder_user["user"].id,
        title="Found MacBook Pro",
        category="Electronics",
        description="Silver Apple MacBook laptop found in engineering computer lab.",
        color="Silver",
        brand="Apple",
        model="MacBook Pro",
        location="Engineering Building",
        date_found="2026-03-05",
        status="active"
    )
    db.add(found)
    db.commit()

    # Find matches for lost item
    lost_matches = find_matches_for_lost_item(lost.id, db, min_score_threshold=30.0)
    assert lost_matches["matches_count"] >= 1
    assert lost_matches["top_match"]["match_score"] >= 70.0

    # Find matches for found item
    found_matches = find_matches_for_found_item(found.id, db, min_score_threshold=30.0)
    assert found_matches["matches_count"] >= 1


def test_matching_api_endpoints(client, claimant_user, sample_match):
    match = sample_match["match"]
    lost = sample_match["lost"]

    # Trigger matching for lost item
    resp_match = client.post(
        f"/api/ai/matching/lost/{lost.id}",
        headers=claimant_user["headers"]
    )
    assert resp_match.status_code == 200
    data = resp_match.json()
    assert data["matches_count"] >= 1

    # Get match details
    resp_detail = client.get(
        f"/api/ai/matching/{match.id}",
        headers=claimant_user["headers"]
    )
    assert resp_detail.status_code == 200
    detail_data = resp_detail.json()
    assert detail_data["match_id"] == match.id
    assert detail_data["match_score"] > 0
