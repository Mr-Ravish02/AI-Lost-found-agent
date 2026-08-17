import pytest
from app.models.item import LostItem, FoundItem, Match, Notification, AdminAction


def test_admin_dashboard_stats_as_admin(client, admin_user, sample_match):
    response = client.get("/api/admin/dashboard/stats", headers=admin_user["headers"])
    assert response.status_code == 200
    data = response.json()
    assert "total_lost" in data
    assert "total_found" in data
    assert "potential_matches" in data
    assert "pending_reviews" in data
    assert "resolved_cases" in data
    assert data["total_lost"] >= 1
    assert data["total_found"] >= 1


def test_admin_dashboard_stats_forbidden_for_user(client, claimant_user):
    response = client.get("/api/admin/dashboard/stats", headers=claimant_user["headers"])
    assert response.status_code == 403


def test_admin_pending_matches_list(client, admin_user, sample_match):
    response = client.get("/api/admin/matches/pending", headers=admin_user["headers"])
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    match_item = data[0]
    assert "match_id" in match_item
    assert "match_score" in match_item
    assert "confidence_level" in match_item


def test_admin_match_detail(client, admin_user, sample_match):
    match_id = sample_match["match"].id
    response = client.get(f"/api/admin/matches/{match_id}", headers=admin_user["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["match_id"] == match_id
    assert "lost_item" in data
    assert "found_item" in data
    assert "factor_breakdown" in data
    assert "reasons" in data


def test_admin_approve_match_resolves_items_and_notifies(client, admin_user, claimant_user, sample_match, db):
    match_id = sample_match["match"].id
    response = client.post(
        f"/api/admin/matches/{match_id}/approve",
        headers=admin_user["headers"],
        json={"notes": "Physical verification completed in person at helpdesk."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"

    # Verify database state
    db_match = db.query(Match).filter(Match.id == match_id).first()
    assert db_match.status == "approved"
    assert db_match.lost_item.status == "returned"
    assert db_match.found_item.status == "returned"

    # Verify notification created
    notif = db.query(Notification).filter(Notification.user_id == claimant_user["user"].id).first()
    assert notif is not None
    assert "Approved" in notif.title


def test_admin_reject_match(client, admin_user, sample_match, db):
    match_id = sample_match["match"].id
    response = client.post(
        f"/api/admin/matches/{match_id}/reject",
        headers=admin_user["headers"],
        json={"notes": "Serial numbers and physical markings do not match."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"

    db_match = db.query(Match).filter(Match.id == match_id).first()
    assert db_match.status == "rejected"


def test_admin_request_more_info(client, admin_user, sample_match, db):
    match_id = sample_match["match"].id
    response = client.post(
        f"/api/admin/matches/{match_id}/request-info",
        headers=admin_user["headers"],
        json={"notes": "Please provide purchase invoice or serial number photo."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"

    db_match = db.query(Match).filter(Match.id == match_id).first()
    assert db_match.status == "in_progress"


def test_non_admin_cannot_approve_match(client, claimant_user, sample_match):
    match_id = sample_match["match"].id
    response = client.post(
        f"/api/admin/matches/{match_id}/approve",
        headers=claimant_user["headers"],
        json={"notes": "Trying to self-approve"}
    )
    assert response.status_code == 403


def test_notifications_lifecycle(client, claimant_user, db):
    # 1. Create a test notification
    notif = Notification(
        user_id=claimant_user["user"].id,
        title="Test Match Found",
        message="A potential match has been identified.",
        type="match_found",
        is_read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    # 2. Fetch notifications
    res = client.get("/api/notifications", headers=claimant_user["headers"])
    assert res.status_code == 200
    notifs = res.json()
    assert len(notifs) >= 1
    target = next((n for n in notifs if n["id"] == notif.id), None)
    assert target is not None
    assert target["is_read"] is False

    # 3. Mark as read
    read_res = client.patch(f"/api/notifications/{notif.id}/read", headers=claimant_user["headers"])
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True

    # 4. Mark all as read
    mark_all_res = client.post("/api/notifications/mark-all-read", headers=claimant_user["headers"])
    assert mark_all_res.status_code == 200
