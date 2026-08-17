"""
Real End-to-End Demonstration Script
Executes all 13 steps of the complete Lost & Found AI pipeline using real FastAPI TestClient,
real database persistence, real embedding/similarity calculation, real LangGraph workflow,
and real Admin Review approval.
"""
import sys
import json

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from starlette.testclient import TestClient
from app.main import app
from app.database import SessionLocal, Base, engine
from app.models.item import LostItem, FoundItem, Match, Notification, AdminAction

def run_real_e2e_demo():
    print("=" * 70)
    print("AI-POWERED SMART LOST & FOUND - FULL REAL E2E DEMONSTRATION")
    print("=" * 70)

    client = TestClient(app)
    
    # Step 1: Create / Register Claimant and Admin
    print("\n--- STEP 1: Register & Login as Claimant ---")
    claimant_email = "claimant.demo@campus.edu"
    claimant_pass = "SecurePass123!"
    reg_claimant = client.post("/api/auth/register", json={
        "email": claimant_email,
        "password": claimant_pass,
        "full_name": "Aman Kumar (Claimant)",
        "role": "user"
    })
    if reg_claimant.status_code != 200:
        # Try login if exists
        login_res = client.post("/api/auth/login", json={"email": claimant_email, "password": claimant_pass})
    else:
        login_res = reg_claimant
    
    claimant_token = login_res.json()["access_token"]
    claimant_headers = {"Authorization": f"Bearer {claimant_token}"}
    print(f"Claimant Authenticated: {claimant_email} | JWT Token generated.")

    # Register / Login Finder
    finder_email = "finder.demo@campus.edu"
    finder_pass = "SecurePass123!"
    reg_finder = client.post("/api/auth/register", json={
        "email": finder_email,
        "password": finder_pass,
        "full_name": "Staff Officer John",
        "role": "user"
    })
    finder_token = reg_finder.json().get("access_token") if reg_finder.status_code == 200 else client.post("/api/auth/login", json={"email": finder_email, "password": finder_pass}).json()["access_token"]
    finder_headers = {"Authorization": f"Bearer {finder_token}"}

    # Register / Login Admin
    admin_email = "admin.head@campus.edu"
    admin_pass = "AdminSuperPass123!"
    reg_admin = client.post("/api/auth/register", json={
        "email": admin_email,
        "password": admin_pass,
        "full_name": "Security Administrator",
        "role": "admin"
    })
    admin_token = reg_admin.json().get("access_token") if reg_admin.status_code == 200 else client.post("/api/auth/login", json={"email": admin_email, "password": admin_pass}).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print(f"Administrator Authenticated: {admin_email}")

    # Step 2: Create a Lost Item Report
    print("\n--- STEP 2: Create Lost Item Report ---")
    lost_payload = {
        "title": "Black Dell XPS 15 Laptop",
        "category": "Electronics",
        "description": "Black Dell XPS 15 laptop with red sticker on the back lid. Left on 2nd floor library table.",
        "color": "Black",
        "brand": "Dell",
        "model": "XPS 15",
        "location": "Library 2nd Floor Study Room",
        "date_lost": "2026-08-15",
        "distinctive_features": ["red sticker on back lid", "scratch near trackpad"]
    }
    lost_res = client.post("/api/items/lost", json=lost_payload, headers=claimant_headers)
    assert lost_res.status_code in [200, 201], lost_res.text
    lost_item = lost_res.json()
    lost_id = lost_item["id"]
    print(f"Lost Item Created: #{lost_id} '{lost_item['title']}' | Status: {lost_item['status']}")

    # Step 3: Create a Matching Found Item Report
    print("\n--- STEP 3: Create Matching Found Item Report ---")
    found_payload = {
        "title": "Found Dell XPS Laptop in Library",
        "category": "Electronics",
        "description": "Black Dell laptop found on library table. Red sticker on lid. Has a blue USB drive inside sleeve.",
        "color": "Black",
        "brand": "Dell",
        "model": "XPS",
        "location": "Main Library Table #4",
        "date_found": "2026-08-15",
        "distinctive_features": ["red sticker", "blue SanDisk USB drive in sleeve"]
    }
    found_res = client.post("/api/items/found", json=found_payload, headers=finder_headers)
    assert found_res.status_code in [200, 201], found_res.text
    found_item = found_res.json()
    found_id = found_item["id"]
    print(f"Found Item Created: #{found_id} '{found_item['title']}' | Status: {found_item['status']}")

    # Step 4: Trigger AI Matching Workflow
    print("\n--- STEP 4: Trigger AI Matching (LangGraph Workflow) ---")
    workflow_res = client.post(f"/api/ai/workflow/lost/{lost_id}", headers=claimant_headers)
    assert workflow_res.status_code == 200, workflow_res.text
    workflow_data = workflow_res.json()

    # Step 5: Verify High-Confidence Match
    print("\n--- STEP 5: Verify AI Match Result ---")
    match_score = workflow_data["match_score"]
    confidence = workflow_data["confidence"]
    print(f"AI Match Score: {match_score}%")
    print(f"Confidence Level: {confidence.upper()}")
    print(f"Workflow Status: {workflow_data['workflow_status']}")
    print(f"Recommendation: {workflow_data['recommendation']}")
    assert match_score >= 70.0, f"Expected high score, got {match_score}"
    assert confidence in ["high", "medium"]

    # Step 6: Generate / Verify Verification Questions
    print("\n--- STEP 6: Verification Questions Generated ---")
    questions = workflow_data.get("verification_questions", [])
    print(f"Generated {len(questions)} safe verification questions:")
    for idx, q in enumerate(questions):
        print(f"  Q{idx+1}: {q.get('question_text') or q.get('question')}")
    assert len(questions) >= 3

    # Step 7: Submit Verification Answers
    print("\n--- STEP 7: Submit Claimant Verification Answers ---")
    answers_payload = [
        {
            "question_id": q["id"],
            "answer_text": "Dell XPS 15 black laptop with red sticker on lid lost in library study room."
        }
        for q in questions
    ]
    verify_res = client.post(f"/api/ai/workflow/lost/{lost_id}/verify", headers=claimant_headers, json={"answers": answers_payload})
    assert verify_res.status_code == 200, verify_res.text
    verify_data = verify_res.json()
    v_score = verify_data["verification_score"]
    print(f"Answer Evaluation Completed.")
    print(f"Verification Score: {v_score}%")
    print(f"Workflow Status Transitioned To: {verify_data['workflow_status']}")
    assert verify_data["workflow_status"] == "admin_review"

    # Step 8 & 9: Login as Admin & Open Admin Dashboard
    print("\n--- STEP 8 & 9: Admin Dashboard & Stats ---")
    stats_res = client.get("/api/admin/dashboard/stats", headers=admin_headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    print(f"Admin Dashboard Stats: Total Lost: {stats['total_lost']} | Total Found: {stats['total_found']} | Pending Reviews: {stats['pending_reviews']} | Resolved: {stats['resolved_cases']}")

    pending_res = client.get("/api/admin/matches/pending", headers=admin_headers)
    assert pending_res.status_code == 200
    pending_list = pending_res.json()
    print(f"Found {len(pending_list)} pending matches in administrator queue.")
    target_match = next((m for m in pending_list if m["lost_item"].get("id") == lost_id), pending_list[0])
    match_id = target_match["match_id"]

    # Step 10: Admin Review Match Dossier
    print(f"\n--- STEP 10: Review Match Dossier (Match #{match_id}) ---")
    detail_res = client.get(f"/api/admin/matches/{match_id}", headers=admin_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    print(f"Match Score: {detail['match_score']}% | Verification Score: {detail['verification_score']}%")
    print(f"Factors: {json.dumps(detail['factor_breakdown'])}")
    print(f"Matching Reasons: {detail['reasons']}")
    print(f"Verification Answers Count: {len(detail['answers'])}")

    # Step 11: Admin Approves Match
    print("\n--- STEP 11: Administrator Approves Match ---")
    approve_res = client.post(f"/api/admin/matches/{match_id}/approve", headers=admin_headers, json={
        "notes": "Verified ownership in person. Red sticker and scratch match claimant description. Handed over."
    })
    assert approve_res.status_code == 200
    print(f"Approval Result: {approve_res.json()['message']} | Status: {approve_res.json()['status']}")

    # Step 12: Verify Item Status Changes to Resolved / Returned
    print("\n--- STEP 12: Verify Item Status Lifecycle ---")
    lost_check = client.get(f"/api/items/lost/{lost_id}", headers=claimant_headers).json()
    found_check = client.get(f"/api/items/found/{found_id}", headers=finder_headers).json()
    print(f"Lost Item #{lost_id} Status: {lost_check['status'].upper()} (Expected: RETURNED)")
    print(f"Found Item #{found_id} Status: {found_check['status'].upper()} (Expected: RETURNED)")
    assert lost_check["status"] == "returned"
    assert found_check["status"] == "returned"

    # Step 13: Verify User Notifications
    print("\n--- STEP 13: Verify User Notifications ---")
    notifs_res = client.get("/api/notifications", headers=claimant_headers)
    assert notifs_res.status_code == 200
    notifs = notifs_res.json()
    print(f"Claimant received {len(notifs)} notifications:")
    for n in notifs:
        print(f"  [{n['type'].upper()}] {n['title']} — {n['message']}")
    
    assert any("Approved" in n["title"] or "approved" in n["message"] for n in notifs)

    print("\n" + "=" * 70)
    print("REAL END-TO-END DEMONSTRATION PASSED 100% SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_real_e2e_demo()
