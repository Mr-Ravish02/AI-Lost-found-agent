import pytest
from app.agents.extraction_agent import rule_based_extract, extract_item_attributes


def test_auth_registration_and_login(client):
    # Register
    reg_resp = client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "SecurePassword123",
            "full_name": "New User",
            "role": "user"
        }
    )
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert "access_token" in user_data

    # Login
    login_resp = client.post(
        "/api/auth/login",
        json={
            "email": "newuser@example.com",
            "password": "SecurePassword123"
        }
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data


def test_lost_and_found_items_crud(client, claimant_user):
    headers = claimant_user["headers"]

    # 1. Create Lost Item
    lost_resp = client.post(
        "/api/items/lost",
        headers=headers,
        json={
            "title": "Black Umbrella",
            "category": "Accessories",
            "description": "Black foldable umbrella left near lecture hall 101.",
            "color": "Black",
            "brand": "Totes",
            "location": "Lecture Hall 101",
            "date_lost": "2026-03-01",
            "distinctive_features": ["Wooden handle"]
        }
    )
    assert lost_resp.status_code == 201
    lost_item = lost_resp.json()
    assert lost_item["title"] == "Black Umbrella"
    lost_id = lost_item["id"]

    # 2. Read Lost Item
    get_lost = client.get(f"/api/items/lost/{lost_id}", headers=headers)
    assert get_lost.status_code == 200

    # 3. Create Found Item
    found_resp = client.post(
        "/api/items/found",
        headers=headers,
        json={
            "title": "Found Black Umbrella",
            "category": "Accessories",
            "description": "Found foldable umbrella near entrance.",
            "color": "Black",
            "brand": "Totes",
            "location": "Campus Entrance",
            "date_found": "2026-03-01",
            "distinctive_features": ["Wooden handle"]
        }
    )
    assert found_resp.status_code == 201
    found_id = found_resp.json()["id"]

    # 4. List items
    list_lost = client.get("/api/items/lost", headers=headers)
    assert list_lost.status_code == 200
    assert len(list_lost.json()) >= 1


def test_extraction_agent_deterministic_fallback():
    title = "Lost Red Beats Headphones"
    desc = "Red Beats Studio wireless headphones left in library 3rd floor. Has a small scratch on left ear cup."
    
    extracted = rule_based_extract(f"{title} {desc}")
    assert extracted["category"] == "Electronics"
    assert extracted["color"] == "Red"
    assert extracted["brand"] == "Beats"
    assert len(extracted["distinctive_features"]) >= 1
