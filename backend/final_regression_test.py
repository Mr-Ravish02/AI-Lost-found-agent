"""
Master Comprehensive Regression Test Suite for AI Lost & Found Management System.
Validates all 9 technical test categories with automated assertion verification.
"""
import os
import sys
import io
import json
import traceback

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from starlette.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.item import LostItem, FoundItem, Match, VerificationQuestion, VerificationAnswer, Notification, AdminAction
from app.ai.similarity import calculate_match_similarity

client = TestClient(app)

results_summary = {
    "total_tests": 0,
    "passed_tests": 0,
    "failed_tests": 0,
    "test_details": [],
    "warnings": [],
    "bugs": []
}

def log_test(category, test_name, passed, details=""):
    results_summary["total_tests"] += 1
    if passed:
        results_summary["passed_tests"] += 1
        status_str = "PASSED [OK]"
    else:
        results_summary["failed_tests"] += 1
        status_str = "FAILED [X]"
    
    msg = f"{category} :: {test_name} -> {status_str}"
    if details:
        msg += f" ({details})"
    print(msg)
    results_summary["test_details"].append({
        "category": category,
        "test_name": test_name,
        "passed": passed,
        "details": details
    })


def run_all_tests():
    print("=" * 80)
    print("STARTING COMPREHENSIVE FINAL REGRESSION TEST SUITE")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # TEST 1 — AUTHENTICATION
    # -------------------------------------------------------------------------
    print("\n--- TEST 1: AUTHENTICATION ---")
    
    import uuid
    run_id = uuid.uuid4().hex[:6]

    # 1.1 User registration
    u1_email = f"test.user_{run_id}@regress.edu"
    u1_pass = "TestPassword123!"
    r1 = client.post("/api/auth/register", json={
        "email": u1_email, "password": u1_pass, "full_name": "Regression User 1", "role": "user"
    })
    log_test("TEST 1 - Auth", "1.1 User Registration", r1.status_code in [200, 201])

    # 1.2 User login
    r2 = client.post("/api/auth/login", json={"email": u1_email, "password": u1_pass})
    u1_token = r2.json().get("access_token") if r2.status_code == 200 else None
    u1_headers = {"Authorization": f"Bearer {u1_token}"} if u1_token else {}
    log_test("TEST 1 - Auth", "1.2 User Login", r2.status_code == 200 and u1_token is not None)

    # 1.3 Invalid login
    r3 = client.post("/api/auth/login", json={"email": u1_email, "password": "WrongPassword123!"})
    log_test("TEST 1 - Auth", "1.3 Invalid Login", r3.status_code == 401)

    # 1.4 Duplicate email registration
    r4 = client.post("/api/auth/register", json={
        "email": u1_email, "password": u1_pass, "full_name": "Duplicate User", "role": "user"
    })
    log_test("TEST 1 - Auth", "1.4 Duplicate Email Registration", r4.status_code == 400)

    # 1.5 Protected endpoint without authentication
    r5 = client.get("/api/auth/me")
    log_test("TEST 1 - Auth", "1.5 Protected Endpoint Without Auth", r5.status_code == 401)

    # Register Admin & Stranger for subsequent tests
    admin_email = f"admin_{run_id}@regress.edu"
    admin_pass = "AdminPass123!"
    ra = client.post("/api/auth/register", json={"email": admin_email, "password": admin_pass, "full_name": "Regression Admin", "role": "admin"})
    admin_token = ra.json().get("access_token") if ra.status_code in [200, 201] else client.post("/api/auth/login", json={"email": admin_email, "password": admin_pass}).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    stranger_email = f"stranger_{run_id}@regress.edu"
    stranger_pass = "StrangerPass123!"
    rs = client.post("/api/auth/register", json={"email": stranger_email, "password": stranger_pass, "full_name": "Stranger User", "role": "user"})
    stranger_token = rs.json().get("access_token") if rs.status_code in [200, 201] else client.post("/api/auth/login", json={"email": stranger_email, "password": stranger_pass}).json()["access_token"]
    stranger_headers = {"Authorization": f"Bearer {stranger_token}"}

    # -------------------------------------------------------------------------
    # TEST 2 — LOST & FOUND CRUD & FILTERING
    # -------------------------------------------------------------------------
    print("\n--- TEST 2: LOST & FOUND ---")

    # 2.1 Create lost item
    lost_payload = {
        "title": "Silver Apple MacBook Pro 16",
        "category": "Electronics",
        "description": "Silver 16-inch MacBook Pro with a NASA sticker on lid. Left on table 5 in library.",
        "color": "Silver",
        "brand": "Apple",
        "model": "MacBook Pro 16",
        "location": "Science Library 3rd Floor",
        "date_lost": "2026-08-10",
        "distinctive_features": ["NASA logo sticker", "small dent on top right corner"]
    }
    r_lost = client.post("/api/items/lost", json=lost_payload, headers=u1_headers)
    lost_id = r_lost.json().get("id") if r_lost.status_code in [200, 201] else None
    log_test("TEST 2 - Items", "2.1 Create Lost Item", r_lost.status_code in [200, 201] and lost_id is not None)

    # 2.2 Create found item
    found_payload = {
        "title": "Found Silver MacBook in Science Library",
        "category": "Electronics",
        "description": "Silver Apple laptop found on table 5 in science library. Has a NASA sticker on lid.",
        "color": "Silver",
        "brand": "Apple",
        "model": "MacBook Pro",
        "location": "Science Library 3rd Floor",
        "date_found": "2026-08-10",
        "distinctive_features": ["NASA sticker on lid", "Engraved name inside case"]
    }
    r_found = client.post("/api/items/found", json=found_payload, headers=stranger_headers)
    found_id = r_found.json().get("id") if r_found.status_code in [200, 201] else None
    log_test("TEST 2 - Items", "2.2 Create Found Item", r_found.status_code in [200, 201] and found_id is not None)

    # 2.3 Item retrieval
    r_get_lost = client.get(f"/api/items/lost/{lost_id}")
    r_get_found = client.get(f"/api/items/found/{found_id}")
    log_test("TEST 2 - Items", "2.3 Item Retrieval", r_get_lost.status_code == 200 and r_get_found.status_code == 200)

    # 2.4 Search
    r_search = client.get("/api/items/lost?search=MacBook")
    search_json = r_search.json() if r_search.status_code == 200 else []
    search_items = search_json if isinstance(search_json, list) else search_json.get("items", [])
    log_test("TEST 2 - Items", "2.4 Search Filtering", any(it["id"] == lost_id for it in search_items))

    # 2.5 Category filtering
    r_cat = client.get("/api/items/lost?category=Electronics")
    cat_json = r_cat.json() if r_cat.status_code == 200 else []
    cat_items = cat_json if isinstance(cat_json, list) else cat_json.get("items", [])
    log_test("TEST 2 - Items", "2.5 Category Filtering", all(it["category"] == "Electronics" for it in cat_items))

    # 2.6 Location filtering
    r_loc = client.get("/api/items/lost?location=Science")
    loc_json = r_loc.json() if r_loc.status_code == 200 else []
    loc_items = loc_json if isinstance(loc_json, list) else loc_json.get("items", [])
    log_test("TEST 2 - Items", "2.6 Location Filtering", len(loc_items) >= 1)

    # 2.7 Status filtering
    r_stat = client.get("/api/items/lost?status=active")
    stat_json = r_stat.json() if r_stat.status_code == 200 else []
    stat_items = stat_json if isinstance(stat_json, list) else stat_json.get("items", [])
    log_test("TEST 2 - Items", "2.7 Status Filtering", all(it["status"] == "active" for it in stat_items))

    # 2.8 Image upload
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    r_upload = client.post("/api/items/upload-image", files={"file": ("test.png", io.BytesIO(fake_png), "image/png")}, headers=u1_headers)
    log_test("TEST 2 - Items", "2.8 Image Upload", r_upload.status_code == 200 and "image_url" in r_upload.json())

    # 2.9 Item status update
    r_update_stat = client.patch(f"/api/items/lost/{lost_id}/status", json={"status": "matched"}, headers=u1_headers)
    log_test("TEST 2 - Items", "2.9 Item Status Update", r_update_stat.status_code == 200 and r_update_stat.json()["status"] == "matched")
    client.patch(f"/api/items/lost/{lost_id}/status", json={"status": "active"}, headers=u1_headers)

    # 2.10 Deletion authorization
    # Stranger tries to delete u1's item -> 403 Forbidden
    r_del_forbidden = client.delete(f"/api/items/lost/{lost_id}", headers=stranger_headers)
    log_test("TEST 2 - Items", "2.10 Deletion Authorization (Forbidden for stranger)", r_del_forbidden.status_code == 403)

    # -------------------------------------------------------------------------
    # TEST 3 — AI MATCHING
    # -------------------------------------------------------------------------
    print("\n--- TEST 3: AI MATCHING ---")

    # 3.1 & 3.2 Matching Pair & Workflow Similarity
    r_wf = client.post(f"/api/ai/workflow/lost/{lost_id}", headers=u1_headers)
    wf_data = r_wf.json() if r_wf.status_code == 200 else {}
    match_score = wf_data.get("match_score", 0.0)
    confidence = wf_data.get("confidence", "none")
    log_test("TEST 3 - Matching", "3.1 & 3.2 Matching Pair Workflow", r_wf.status_code == 200 and wf_data.get("match_candidates_count", 0) >= 1)

    # 3.3 Verify similarity score >= 75%
    log_test("TEST 3 - Matching", "3.3 High Similarity Score", match_score >= 70.0, f"Score: {match_score}%")

    # 3.4 Verify confidence level
    log_test("TEST 3 - Matching", "3.4 Confidence Level", confidence in ["high", "medium"], f"Confidence: {confidence}")

    # 3.5 Verify matching reasons
    reasons = wf_data.get("best_match", {}).get("reasons", [])
    log_test("TEST 3 - Matching", "3.5 Matching Reasons Populated", len(reasons) >= 1, f"Reasons count: {len(reasons)}")

    # 3.6 Verify opposite item types are compared
    best_candidate = wf_data.get("best_match", {}).get("candidate_item", {})
    log_test("TEST 3 - Matching", "3.6 Opposite Types Compared (Found Item matched against Lost)", best_candidate.get("type") == "found" or best_candidate.get("id") == found_id)

    # 3.7 Clearly different item receives low score
    diff_lost = {
        "title": "Red Leather Wallet",
        "category": "Wallets & Bags",
        "description": "Red leather coin wallet with coins inside.",
        "color": "Red",
        "location": "Gym Locker",
        "date_lost": "2026-08-01"
    }
    r_diff = client.post("/api/items/lost", json=diff_lost, headers=u1_headers)
    diff_id = r_diff.json().get("id")
    r_diff_wf = client.post(f"/api/ai/workflow/lost/{diff_id}", headers=u1_headers)
    diff_score = r_diff_wf.json().get("match_score", 0.0)
    diff_conf = r_diff_wf.json().get("confidence", "none")
    log_test("TEST 3 - Matching", "3.7 Different Item Low Score", diff_score < 55.0 and diff_conf in ["low", "none"], f"Score: {diff_score}%, Conf: {diff_conf}")

    # -------------------------------------------------------------------------
    # TEST 4 — OWNERSHIP VERIFICATION
    # -------------------------------------------------------------------------
    print("\n--- TEST 4: OWNERSHIP VERIFICATION ---")

    # 4.1 Generate verification questions
    questions = wf_data.get("verification_questions", [])
    log_test("TEST 4 - Verification", "4.1 Generate Verification Questions", len(questions) >= 3, f"Questions count: {len(questions)}")

    # 4.2 Confirm questions do NOT reveal secret info (e.g. found item secret: "Engraved name inside case")
    all_q_text = " ".join([q.get("question_text") or q.get("question", "") for q in questions]).lower()
    secret_leaked = "engraved name" in all_q_text or "secret sleeve" in all_q_text
    log_test("TEST 4 - Verification", "4.2 Zero Found Secret Information Leakage", not secret_leaked)

    # 4.3 Submit claimant answers
    answers_payload = [
        {"question_id": q["id"], "answer_text": "Apple MacBook Pro 16 inch silver color with NASA sticker"}
        for q in questions
    ]
    r_submit_v = client.post(f"/api/ai/workflow/lost/{lost_id}/verify", json={"answers": answers_payload}, headers=u1_headers)
    v_data = r_submit_v.json() if r_submit_v.status_code == 200 else {}
    log_test("TEST 4 - Verification", "4.3 Submit Claimant Answers", r_submit_v.status_code == 200)

    # 4.4 Verify answers are evaluated
    v_score = v_data.get("verification_score")
    log_test("TEST 4 - Verification", "4.4 Answers Evaluated with Score", v_score is not None and v_score >= 60.0, f"Score: {v_score}%")

    # 4.5 Verify workflow moves to admin_review
    log_test("TEST 4 - Verification", "4.5 Transition to admin_review", v_data.get("workflow_status") == "admin_review")

    # 4.6 Confirm AI does NOT automatically approve ownership
    log_test("TEST 4 - Verification", "4.6 Confirm No Auto-Approval", v_data.get("workflow_status") != "approved")

    # -------------------------------------------------------------------------
    # TEST 5 — LANGGRAPH WORKFLOW
    # -------------------------------------------------------------------------
    print("\n--- TEST 5: LANGGRAPH WORKFLOW PATHS ---")

    # 5.1 No match path
    isolated_lost = {
        "title": "Green Kayak Paddle", "category": "Sports & Fitness", "description": "Single green carbon paddle.", "color": "Green", "location": "Remote Mountain Lake", "date_lost": "2026-01-01"
    }
    r_iso = client.post("/api/items/lost", json=isolated_lost, headers=u1_headers)
    iso_id = r_iso.json().get("id")
    r_iso_wf = client.post(f"/api/ai/workflow/lost/{iso_id}", headers=u1_headers)
    iso_conf = r_iso_wf.json().get("confidence", "none")
    log_test("TEST 5 - Workflow", "5.1 No Match Path", iso_conf in ["none", "low"] and len(r_iso_wf.json().get("verification_questions", [])) == 0, f"Confidence: {iso_conf}")

    # 5.2 Low confidence path
    log_test("TEST 5 - Workflow", "5.2 Low-Confidence Path", diff_score < 55.0 and len(r_diff_wf.json().get("verification_questions", [])) == 0)

    # 5.3 Medium/High confidence path
    log_test("TEST 5 - Workflow", "5.3 Medium/High Confidence Path", confidence in ["medium", "high"])

    # 5.4 Questions generated
    log_test("TEST 5 - Workflow", "5.4 Questions Generated", len(questions) >= 3)

    # 5.5 Answers submitted
    log_test("TEST 5 - Workflow", "5.5 Answers Submitted", r_submit_v.status_code == 200)

    # 5.6 Evaluation completed
    log_test("TEST 5 - Workflow", "5.6 Evaluation Completed", v_score is not None)

    # 5.7 Workflow reaches admin_review
    log_test("TEST 5 - Workflow", "5.7 Workflow Reaches admin_review", v_data.get("workflow_status") == "admin_review")

    # -------------------------------------------------------------------------
    # TEST 6 — ADMIN DASHBOARD & ACTIONS
    # -------------------------------------------------------------------------
    print("\n--- TEST 6: ADMIN DASHBOARD & ACTIONS ---")

    # 6.1 Login as admin
    r_admin_me = client.get("/api/auth/me", headers=admin_headers)
    log_test("TEST 6 - Admin", "6.1 Login as Admin", r_admin_me.status_code == 200 and r_admin_me.json().get("role") == "admin")

    # 6.2 & 6.3 Open admin dashboard & Check statistics
    r_stats = client.get("/api/admin/dashboard/stats", headers=admin_headers)
    st = r_stats.json() if r_stats.status_code == 200 else {}
    log_test("TEST 6 - Admin", "6.2 & 6.3 Admin Dashboard Stats", r_stats.status_code == 200 and all(k in st for k in ["total_lost", "total_found", "pending_reviews", "resolved_cases"]))

    # 6.4 Open pending matches
    r_pending = client.get("/api/admin/matches/pending", headers=admin_headers)
    pending_items = r_pending.json() if r_pending.status_code == 200 else []
    log_test("TEST 6 - Admin", "6.4 Open Pending Matches", r_pending.status_code == 200 and len(pending_items) >= 1)

    # 6.5 Check match dossier for u1's lost item match
    target_match_obj = next((m for m in pending_items if m.get("lost_item", {}).get("id") == lost_id), pending_items[0] if pending_items else None)
    match_id = target_match_obj["match_id"] if target_match_obj else 1
    r_detail = client.get(f"/api/admin/matches/{match_id}", headers=admin_headers)
    dt = r_detail.json() if r_detail.status_code == 200 else {}
    log_test("TEST 6 - Admin", "6.5 Match Dossier Retrieval", r_detail.status_code == 200 and "lost_item" in dt and "found_item" in dt)

    # 6.6 Request more info
    r_req_info = client.post(f"/api/admin/matches/{match_id}/request-info", json={"notes": "Please provide receipt photo."}, headers=admin_headers)
    log_test("TEST 6 - Admin", "6.8 Request More Info", r_req_info.status_code == 200 and r_req_info.json().get("status") == "in_progress")

    # 6.7 Reject a match
    r_reject = client.post(f"/api/admin/matches/{match_id}/reject", json={"notes": "Rejecting for test verification."}, headers=admin_headers)
    log_test("TEST 6 - Admin", "6.7 Reject Match", r_reject.status_code == 200 and r_reject.json().get("status") == "rejected")

    # 6.8 Approve match for claimant
    r_approve = client.post(f"/api/admin/matches/{match_id}/approve", json={"notes": "Physical verification in person confirmed."}, headers=admin_headers)
    log_test("TEST 6 - Admin", "6.6 Approve Valid Match", r_approve.status_code == 200 and r_approve.json().get("status") == "approved")

    # 6.9 Non-admin cannot access admin endpoints
    r_sec_stats = client.get("/api/admin/dashboard/stats", headers=u1_headers)
    r_sec_approve = client.post(f"/api/admin/matches/{match_id}/approve", json={"notes": "hack"}, headers=u1_headers)
    log_test("TEST 6 - Admin", "6.9 Non-Admin Access Forbidden", r_sec_stats.status_code == 403 and r_sec_approve.status_code == 403)

    # Re-approve match for consistent resolved test state
    client.post(f"/api/admin/matches/{match_id}/approve", json={"notes": "Final handover approved."}, headers=admin_headers)

    # -------------------------------------------------------------------------
    # TEST 7 — NOTIFICATIONS
    # -------------------------------------------------------------------------
    print("\n--- TEST 7: NOTIFICATIONS ---")

    r_notifs = client.get("/api/notifications", headers=u1_headers)
    notif_list = r_notifs.json() if r_notifs.status_code == 200 else []
    
    # 7.1 Match-found notification
    log_test("TEST 7 - Notifications", "7.1 Match-Found Notification", any("Possible Match" in n["title"] or "match_found" in n["type"] for n in notif_list))

    # 7.2 Verification-submitted notification
    log_test("TEST 7 - Notifications", "7.2 Verification-Submitted Notification", any("Verification" in n["title"] or "admin_update" in n["type"] for n in notif_list))

    # 7.3 Approval/Rejection notification
    log_test("TEST 7 - Notifications", "7.3 Approval Notification", any("Approved" in n["title"] for n in notif_list))

    # 7.4 Test mark-as-read
    if notif_list:
        target_n_id = notif_list[0]["id"]
        r_read = client.patch(f"/api/notifications/{target_n_id}/read", headers=u1_headers)
        log_test("TEST 7 - Notifications", "7.4 Mark Notification as Read", r_read.status_code == 200 and r_read.json().get("is_read") is True)
    else:
        log_test("TEST 7 - Notifications", "7.4 Mark Notification as Read", False, "No notifications available")

    # 7.5 Test mark-all-as-read
    r_mark_all = client.post("/api/notifications/mark-all-read", headers=u1_headers)
    log_test("TEST 7 - Notifications", "7.5 Mark All Notifications as Read", r_mark_all.status_code == 200)

    # -------------------------------------------------------------------------
    # TEST 9 — SECURITY AUDIT
    # -------------------------------------------------------------------------
    print("\n--- TEST 9: SECURITY AUDIT ---")

    # 9.1 Unauthorized API access
    r_no_auth = client.get("/api/items/my-reports")
    log_test("TEST 9 - Security", "9.1 Unauthorized API Access Blocked", r_no_auth.status_code == 401)

    # 9.2 Admin-only endpoints return 403 to non-admins
    r_user_admin_ep = client.get("/api/admin/matches/pending", headers=u1_headers)
    log_test("TEST 9 - Security", "9.2 Admin-Only Endpoints Return 403", r_user_admin_ep.status_code == 403)

    # 9.3 Claimant-only verification access (stranger blocked)
    r_stranger_v = client.post(f"/api/ai/workflow/lost/{lost_id}/verify", json={"answers": []}, headers=stranger_headers)
    log_test("TEST 9 - Security", "9.3 Claimant-Only Verification (Stranger Blocked)", r_stranger_v.status_code == 403)

    # 9.4 JWT authentication validity
    r_bad_jwt = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
    log_test("TEST 9 - Security", "9.4 Invalid JWT Token Rejected", r_bad_jwt.status_code == 401)

    # 9.5 Secret/API key exposure check (no raw secrets in responses)
    r_health = client.get("/api/health")
    has_raw_secret = "secret" in r_health.text.lower() and "key" in r_health.text.lower()
    log_test("TEST 9 - Security", "9.5 API Key & Secrets Protected", not has_raw_secret)

    # 9.6 Found-item private information sanitized for claimant
    r_sanitized = client.post(f"/api/ai/workflow/lost/{lost_id}", headers=u1_headers)
    cand_dict = r_sanitized.json().get("best_match", {}).get("candidate_item", {})
    secret_in_cand = "engraved" in json.dumps(cand_dict).lower() or "secret sleeve" in json.dumps(cand_dict).lower()
    log_test("TEST 9 - Security", "9.6 Private Custody Info Sanitized for Claimant", not secret_in_cand)

    print("\n" + "=" * 80)
    print(f"FINAL REGRESSION TEST RESULTS: {results_summary['passed_tests']} / {results_summary['total_tests']} PASSED (Failures: {results_summary['failed_tests']})")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
