import pytest
from app.agents.verification_agent import (
    generate_deterministic_questions,
    generate_verification_questions,
    evaluate_single_answer,
    evaluate_verification_answers,
    detect_item_domain
)
from app.models.item import LostItem, FoundItem, Match, VerificationQuestion, VerificationAnswer
from app.schemas.verification import VerificationAnswerIn


def test_deterministic_question_generation_count_and_types(sample_match):
    lost = sample_match["lost"]
    questions = generate_deterministic_questions(lost)
    
    # Check 3 to 5 questions generated
    assert 3 <= len(questions) <= 5
    
    # Check question types for Electronics
    types = [q["question_type"] for q in questions]
    assert "brand" in types
    assert "color" in types
    assert "location" in types
    assert "feature" in types
    assert "circumstances" in types


def test_deterministic_question_generation_privacy_rule(sample_match):
    """
    Ensure questions do NOT reveal secret info from found report,
    nor reveal the answers to the questions.
    """
    lost = sample_match["lost"]
    found = sample_match["found"]
    questions = generate_deterministic_questions(lost)

    all_q_text = " ".join([q["question_text"].lower() for q in questions])

    # 1. Private details from found report MUST NOT be in questions
    assert "sandisk" not in all_q_text
    assert "sleeve" not in all_q_text
    assert "usb" not in all_q_text

    # 2. Questions should not reveal the specific answers (e.g. asking open-ended questions)
    assert "is it black" not in all_q_text
    assert "is it dell" not in all_q_text
    assert "is there a red sticker" not in all_q_text


def test_money_cash_question_generation_dynamic():
    """
    Ensure money/cash items dynamically produce cash-specific verification questions
    (e.g., amount, container, contents) rather than irrelevant brand/model questions.
    """
    cash_lost = LostItem(
        id=99,
        title="Lost Cash 5000 Rupees",
        category="Other",
        description="Lost 5000 rupees in an envelope near ATM counter with two 500 notes and four 1000 notes.",
        color="White envelope",
        brand=None,
        model=None,
        location="Campus ATM",
        distinctive_features=["white bank envelope", "SBI ATM receipt"]
    )

    domain = detect_item_domain(cash_lost)
    assert domain == "money"

    questions = generate_deterministic_questions(cash_lost)
    assert len(questions) >= 4
    
    types = [q["question_type"] for q in questions]
    assert "amount" in types
    assert "container" in types
    assert "contents" in types

    all_text = " ".join([q["question_text"].lower() for q in questions])
    assert "amount" in all_text or "denominations" in all_text
    assert "envelope" in all_text or "stored" in all_text
    # Ensure it does not ask for brand of money
    assert "brand and model" not in all_text


def test_keys_question_generation_dynamic():
    """
    Ensure keys/badges generate key-specific questions (key count, keychain, vehicle emblem).
    """
    keys_lost = LostItem(
        id=101,
        title="Set of Honda Bike Keys",
        category="Keys & Badges",
        description="Set of 3 keys with a black Honda rubber keychain and room key.",
        location="Parking Lot B",
        distinctive_features=["Honda logo", "silver ring"]
    )

    domain = detect_item_domain(keys_lost)
    assert domain == "keys_badge"

    questions = generate_deterministic_questions(keys_lost)
    types = [q["question_type"] for q in questions]
    assert "keys_detail" in types
    assert "identifier" in types or "feature" in types


def test_documents_cards_question_generation_dynamic():
    """
    Ensure ID cards and documents generate identifier and holder questions.
    """
    id_lost = LostItem(
        id=102,
        title="Lost Student ID Card",
        category="Documents & Cards",
        description="College ID card in a blue plastic card sleeve.",
        location="Student Center",
        distinctive_features=["Blue lanyard", "Department of CS"]
    )

    domain = detect_item_domain(id_lost)
    assert domain == "documents_cards"

    questions = generate_deterministic_questions(id_lost)
    types = [q["question_type"] for q in questions]
    assert "identifier" in types
    assert "container" in types


def test_generate_verification_questions_db_persistence_and_status(db, sample_match):
    match = sample_match["match"]
    assert match.status == "pending"

    # Generate questions
    questions = generate_verification_questions(match, db)
    assert 3 <= len(questions) <= 5

    # Check persistence in DB
    db_questions = db.query(VerificationQuestion).filter(VerificationQuestion.match_id == match.id).all()
    assert len(db_questions) == len(questions)

    # Check match status transitioned to in_progress
    db.refresh(match)
    assert match.status == "in_progress"

    # Repeated calls should return existing questions without duplicating
    repeated_questions = generate_verification_questions(match, db)
    assert len(repeated_questions) == len(questions)
    assert db.query(VerificationQuestion).filter(VerificationQuestion.match_id == match.id).count() == len(questions)


def test_weak_match_question_generation_safe(db, claimant_user, finder_user):
    """
    Weak matches should still generate safe, standard verification questions
    based on the lost report without misleading the claimant.
    """
    lost_obj = LostItem(
        user_id=claimant_user["user"].id,
        title="Generic Water Bottle",
        category="Bottles",
        description="Blue insulated stainless steel water bottle lost in cafeteria.",
        color="Blue",
        brand="Hydro Flask",
        model=None,
        location="Cafeteria",
        date_lost="2026-03-02",
        distinctive_features=["Dented bottom"],
        status="active"
    )
    db.add(lost_obj)
    db.commit()
    db.refresh(lost_obj)

    found_obj = FoundItem(
        user_id=finder_user["user"].id,
        title="Found Metal Bottle",
        category="Bottles",
        description="Silver thermos found in gym locker room with gym sticker.",
        color="Silver",
        brand="Generic",
        model=None,
        location="Gym",
        date_found="2026-03-02",
        distinctive_features=["Gym logo sticker"],
        status="active"
    )
    db.add(found_obj)
    db.commit()
    db.refresh(found_obj)

    weak_match = Match(
        lost_item_id=lost_obj.id,
        found_item_id=found_obj.id,
        match_score=40.0,
        confidence_level="low",
        reasons=["Category match: Bottles"],
        status="pending"
    )
    db.add(weak_match)
    db.commit()
    db.refresh(weak_match)

    questions = generate_verification_questions(weak_match, db)
    assert 3 <= len(questions) <= 5

    # Check that found-item details (e.g. gym, silver, gym logo sticker) are NOT in the questions
    q_texts = " ".join([q.question_text.lower() for q in questions])
    assert "gym" not in q_texts
    assert "silver" not in q_texts


def test_evaluate_single_answer(sample_match):
    lost = sample_match["lost"]
    found = sample_match["found"]

    brand_q = VerificationQuestion(id=1, match_id=1, question_text="What is the brand?", question_type="brand")
    color_q = VerificationQuestion(id=2, match_id=1, question_text="What is the color?", question_type="color")
    feature_q = VerificationQuestion(id=3, match_id=1, question_text="What distinctive markings?", question_type="feature")

    # Correct brand answer
    brand_eval = evaluate_single_answer(brand_q, "It is a Dell XPS laptop", lost, found)
    assert brand_eval["score"] >= 70.0

    # Wrong brand answer
    wrong_brand_eval = evaluate_single_answer(brand_q, "It is an Apple MacBook Air", lost, found)
    assert wrong_brand_eval["score"] < 50.0

    # Correct color answer
    color_eval = evaluate_single_answer(color_q, "Black matte finish", lost, found)
    assert color_eval["score"] >= 60.0

    # Feature answer matching distinctive markings
    feature_eval = evaluate_single_answer(feature_q, "It has a red sticker on the back", lost, found)
    assert feature_eval["score"] >= 70.0


def test_evaluate_money_answers():
    """
    Verify amount and container answer evaluation for cash/money items.
    """
    lost_cash = LostItem(
        id=201,
        title="Lost 5000 Cash",
        category="Other",
        description="Lost 5000 rupees in a white envelope near ATM.",
        color="White",
        location="ATM Lobby",
        distinctive_features=["white envelope", "5000 rs"]
    )
    found_cash = FoundItem(
        id=202,
        title="Found Cash in Envelope",
        category="Other",
        description="White envelope containing 5000 rupees found on ATM shelf.",
        color="White",
        location="ATM Lobby",
        distinctive_features=["envelope with 5000 cash"]
    )

    amount_q = VerificationQuestion(id=10, match_id=5, question_text="What was the amount?", question_type="amount")
    container_q = VerificationQuestion(id=11, match_id=5, question_text="How was it stored?", question_type="container")

    # Correct amount answer
    amount_eval = evaluate_single_answer(amount_q, "Total was 5000 rupees with ten 500 notes", lost_cash, found_cash)
    assert amount_eval["score"] >= 75.0

    # Wrong amount answer
    wrong_amount_eval = evaluate_single_answer(amount_q, "It was only 200 dollars", lost_cash, found_cash)
    assert wrong_amount_eval["score"] < 50.0

    # Correct container answer
    container_eval = evaluate_single_answer(container_q, "Stored inside a white paper envelope", lost_cash, found_cash)
    assert container_eval["score"] >= 75.0


def test_evaluate_verification_answers_transitions_to_admin_review(db, sample_match, claimant_user):
    match = sample_match["match"]
    questions = generate_verification_questions(match, db)

    answers_in = []
    for q in questions:
        if q.question_type == "brand":
            answers_in.append(VerificationAnswerIn(question_id=q.id, answer_text="Dell XPS 15"))
        elif q.question_type == "color":
            answers_in.append(VerificationAnswerIn(question_id=q.id, answer_text="Black with dark grey accents"))
        elif q.question_type == "location":
            answers_in.append(VerificationAnswerIn(question_id=q.id, answer_text="Library second floor study table"))
        elif q.question_type == "feature":
            answers_in.append(VerificationAnswerIn(question_id=q.id, answer_text="Red sticker and minor scratch"))
        else:
            answers_in.append(VerificationAnswerIn(question_id=q.id, answer_text="Lost on March 1st 2026"))

    result = evaluate_verification_answers(
        match=match,
        answers_in=answers_in,
        user_id=claimant_user["user"].id,
        db=db
    )

    assert result["match_id"] == match.id
    assert result["verification_score"] > 60.0
    assert result["confidence"] in ["medium", "high"]
    assert result["recommendation"] == "administrator_review"

    # CRITICAL: Status must be admin_review and NEVER auto-approved!
    assert result["status"] == "admin_review"
    db.refresh(match)
    assert match.status == "admin_review"

    # Verify answers stored in DB
    db_answers = db.query(VerificationAnswer).filter(VerificationAnswer.user_id == claimant_user["user"].id).all()
    assert len(db_answers) == len(answers_in)
    for a in db_answers:
        assert a.evaluation_score is not None
        assert a.evaluation_feedback is not None
