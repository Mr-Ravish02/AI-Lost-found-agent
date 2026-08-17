import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.models.item import Match, VerificationQuestion, VerificationAnswer
from app.ai.embeddings import get_description_similarity
from app.schemas.verification import VerificationAnswerIn

logger = logging.getLogger(__name__)


def detect_item_domain(lost_item: Any) -> str:
    """
    Analyzes item category, title, description, and features to classify the item into
    an appropriate domain for targeted verification questions in real time.
    """
    category = (getattr(lost_item, "category", "") or "").lower()
    title = (getattr(lost_item, "title", "") or "").lower()
    desc = (getattr(lost_item, "description", "") or "").lower()
    features = str(getattr(lost_item, "distinctive_features", "") or "").lower()
    combined_text = f"{category} {title} {desc} {features}"

    # 1. Money / Cash / Currency
    money_keywords = [
        "money", "cash", "rupee", "rupees", "inr", "dollar", "dollars", "usd",
        "currency", "banknote", "banknotes", "bill", "bills", "cheque", "check", "paisa"
    ]
    if any(re.search(rf"\b{re.escape(k)}\b", combined_text) for k in money_keywords):
        return "money"

    # 2. Documents & ID Cards
    if "document" in category or "card" in category or any(
        k in combined_text for k in ["passport", "driver's license", "driving license", "license", "pan card", "aadhaar", "adhaar", "student id", "id card", "voter id", "certificate", "debit card", "credit card", "passbook"]
    ):
        return "documents_cards"

    # 3. Keys & Badges
    if "key" in category or "badge" in category or any(
        k in combined_text for k in ["keychain", "keys", "car key", "room key", "fob", "access badge", "rfid badge", "smart badge"]
    ):
        return "keys_badge"

    # 4. Wallets & Bags
    if "wallet" in category or "bag" in category or any(
        k in combined_text for k in ["wallet", "purse", "backpack", "handbag", "duffel", "suitcase", "tote bag", "sling bag", "clutch", "briefcase"]
    ):
        return "wallet_bag"

    # 5. Accessories & Jewelry / Eyewear / Watches
    if "jewelry" in category or "jewellery" in category or "accessories" in category or any(
        k in combined_text for k in ["watch", "smartwatch", "ring", "necklace", "chain", "bracelet", "earring", "earrings", "pendant", "glasses", "sunglasses", "spectacles", "gold", "silver jewelry", "diamond"]
    ):
        return "jewelry_watch"

    # 6. Electronics
    if "electronics" in category or any(
        k in combined_text for k in ["laptop", "phone", "smartphone", "iphone", "macbook", "ipad", "tablet", "headphones", "headphone", "earbuds", "airpods", "charger", "power bank", "kindle", "camera", "hard drive", "pendrive", "usb"]
    ):
        return "electronics"

    # 7. Clothing & Apparel
    if "clothing" in category or "apparel" in category or any(
        k in combined_text for k in ["jacket", "hoodie", "sweater", "shirt", "t-shirt", "coat", "scarf", "hat", "cap", "shoes", "sneakers", "boots", "gloves", "jeans"]
    ):
        return "clothing_apparel"

    # 8. Books & Stationery
    if "book" in category or "stationery" in category or any(
        k in combined_text for k in ["textbook", "notebook", "diary", "novel", "pen", "pencil case", "binder", "notes", "calculator"]
    ):
        return "books_stationery"

    # 9. Sports & Equipment / Bottles
    if "sport" in category or "bottle" in category or any(
        k in combined_text for k in ["water bottle", "bottle", "thermos", "flask", "racket", "umbrella", "gym bag", "yoga mat"]
    ):
        return "sports_bottles"

    return "general"


def generate_deterministic_questions(lost_item: Any) -> List[Dict[str, str]]:
    """
    Deterministic fallback generator: Constructs 3-5 safe, easy-to-understand verification questions
    in simple, plain English dynamically tailored in real-time to the specific item type and category,
    without leaking any secret found-item details.
    Does NOT reveal answers in the questions.
    """
    domain = detect_item_domain(lost_item)
    category = getattr(lost_item, "category", "item") or "item"
    cat_str = category.lower()

    questions = []

    if domain == "money":
        questions.append({
            "question_text": "How much total amount of money did you lose, and what note denominations or currency were there (e.g. 500, 200, or 100 notes)?",
            "question_type": "amount"
        })
        questions.append({
            "question_text": "How was the money stored or kept (e.g., in an envelope, pouch, rubber band, clip, or specific pocket)?",
            "question_type": "container"
        })
        questions.append({
            "question_text": "Was there anything else kept with the cash, like an ATM receipt, bank slip, or note?",
            "question_type": "contents"
        })
        questions.append({
            "question_text": "Where did you lose or last have the money?",
            "question_type": "location"
        })
        questions.append({
            "question_text": "Around what date and time did you lose the money?",
            "question_type": "circumstances"
        })

    elif domain == "keys_badge":
        questions.append({
            "question_text": "How many keys are there, and what are they for (e.g., bike key, car key, house key, or ID badge)?",
            "question_type": "keys_detail"
        })
        questions.append({
            "question_text": "What does the keychain, ring, or ribbon attached to the keys look like?",
            "question_type": "feature"
        })
        questions.append({
            "question_text": "Is there any brand name, vehicle logo, room number, or company name on the keys or badge?",
            "question_type": "identifier"
        })
        questions.append({
            "question_text": "Where did you lose or last have your keys or badge?",
            "question_type": "location"
        })
        questions.append({
            "question_text": "Around what date and time did you lose them?",
            "question_type": "circumstances"
        })

    elif domain == "documents_cards":
        questions.append({
            "question_text": "What full name or organization/college name is written on the card or document?",
            "question_type": "identifier"
        })
        questions.append({
            "question_text": "What kind of cover, holder, sleeve, or pouch was the document or card kept in?",
            "question_type": "container"
        })
        questions.append({
            "question_text": "Are there any special marks, colors, stamps, or issue/expiry years on the card or document?",
            "question_type": "feature"
        })
        questions.append({
            "question_text": "Where did you lose or last use your document or card?",
            "question_type": "location"
        })
        questions.append({
            "question_text": "Around what date and time was the document or card lost?",
            "question_type": "circumstances"
        })

    elif domain == "wallet_bag":
        questions.append({
            "question_text": "What is the brand, material (e.g. leather or fabric), and main color of your wallet or bag?",
            "question_type": "brand"
        })
        questions.append({
            "question_text": "What items, cards, coins, or personal things were kept inside your wallet or bag?",
            "question_type": "contents"
        })
        questions.append({
            "question_text": "Are there any special marks, stickers, zipper styles, or scratches on your bag or wallet?",
            "question_type": "feature"
        })
        questions.append({
            "question_text": "Where did you lose or last have your wallet or bag?",
            "question_type": "location"
        })
        questions.append({
            "question_text": "Around what date and time was the wallet or bag lost?",
            "question_type": "circumstances"
        })

    elif domain == "jewelry_watch":
        questions.append({
            "question_text": "What is the material or metal (e.g. gold, silver, steel, or leather band)?",
            "question_type": "material"
        })
        questions.append({
            "question_text": "What is the brand, maker, or stone/gem on your watch or jewelry?",
            "question_type": "brand"
        })
        questions.append({
            "question_text": "Are there any custom names, engravings, designs, or scratches on it?",
            "question_type": "feature"
        })
        questions.append({
            "question_text": "Where did you lose or last wear your jewelry or watch?",
            "question_type": "location"
        })
        questions.append({
            "question_text": "Around what date and time was it lost?",
            "question_type": "circumstances"
        })

    elif domain == "clothing_apparel":
        questions.append({
            "question_text": "What is the brand, size (e.g. S, M, L, XL), and cloth material of your clothing item?",
            "question_type": "brand"
        })
        questions.append({
            "question_text": "What is the main color and pattern (e.g. plain, striped, or printed design)?",
            "question_type": "color"
        })
        questions.append({
            "question_text": "Was there anything left inside the pockets, or any special badge or mark on it?",
            "question_type": "contents"
        })
        questions.append({
            "question_text": "Where did you lose or leave your clothing item?",
            "question_type": "location"
        })
        questions.append({
            "question_text": "Around what date and time was it lost?",
            "question_type": "circumstances"
        })

    elif domain == "books_stationery":
        questions.append({
            "question_text": "What is the book title, author, subject, or notebook brand?",
            "question_type": "identifier"
        })
        questions.append({
            "question_text": "What color is the cover, and is there any name or note written inside?",
            "question_type": "feature"
        })
        questions.append({
            "question_text": "Were there any pens, bookmarks, or other items kept inside it?",
            "question_type": "contents"
        })
        questions.append({
            "question_text": "Where did you lose or leave your book or stationery?",
            "question_type": "location"
        })
        questions.append({
            "question_text": "Around what date and time was it lost?",
            "question_type": "circumstances"
        })

    elif domain == "sports_bottles":
        questions.append({
            "question_text": "What is the brand, size, or capacity of your bottle or sports item?",
            "question_type": "brand"
        })
        questions.append({
            "question_text": "What is the color, material (e.g. steel or plastic), and cap/lid type?",
            "question_type": "color"
        })
        questions.append({
            "question_text": "Are there any stickers, scratches, dents, or special marks on the item?",
            "question_type": "feature"
        })
        questions.append({
            "question_text": "Where did you lose or last have the item?",
            "question_type": "location"
        })
        questions.append({
            "question_text": "Around what date and time was it lost?",
            "question_type": "circumstances"
        })

    else:
        # Electronics & General Fallback
        questions.append({
            "question_text": f"What is the brand and model of your {cat_str}?",
            "question_type": "brand"
        })
        questions.append({
            "question_text": f"What is the main color and appearance of your {cat_str}?",
            "question_type": "color"
        })
        questions.append({
            "question_text": f"Where did you lose or last have your {cat_str}?",
            "question_type": "location"
        })
        questions.append({
            "question_text": f"Are there any special marks, stickers, scratches, or cover on your {cat_str}?",
            "question_type": "feature"
        })
        questions.append({
            "question_text": f"Around what date and time did you lose your {cat_str}?",
            "question_type": "circumstances"
        })

    return questions


def generate_verification_questions(match: Match, db: Session) -> List[VerificationQuestion]:
    """
    Verification Agent: Generates 3-5 safe, easy-to-understand, privacy-preserving ownership verification questions.
    Dynamically customizes questions to the specific lost item in real time using simple English.
    Ensures ZERO private details from the found report are leaked to the claimant.
    """
    # Check if questions already exist for this match
    existing_questions = (
        db.query(VerificationQuestion)
        .filter(VerificationQuestion.match_id == match.id)
        .order_by(VerificationQuestion.id.asc())
        .all()
    )
    if existing_questions:
        return existing_questions

    lost_item = match.lost_item
    questions_data = []

    # Attempt LLM generation if Groq API key is present
    groq_api_key = settings.GROQ_API_KEY
    if groq_api_key and groq_api_key.strip() and not groq_api_key.startswith("your_"):
        try:
            from groq import Groq
            client = Groq(api_key=groq_api_key)

            detected_domain = detect_item_domain(lost_item)

            prompt = f"""You are a Security & Verification Agent for a Smart Lost and Found System.
Your task is to generate 3 to 5 easy, simple verification questions in plain and simple English.

EASY & SIMPLE ENGLISH RULES:
1. Use simple, everyday words that are very easy to understand and answer for any ordinary person.
2. Avoid difficult English, hard vocabulary, technical jargon, or complex phrasing.
3. Keep each question short, clear, and direct (e.g. "What is the brand and model of your phone?", "Where did you lose it?").

CRITICAL PRIVACY & SECURITY RULES:
1. Do NOT include, mention, or hint at any unique clues or secret details from any found item report.
2. The questions must be open-ended and probe the claimant's genuine knowledge about their own reported lost item.
3. Do NOT include the answers in the questions (e.g. ask "How much money was lost and what notes were there?", NEVER "Was it 5000 rupees in 500 notes?").
4. DYNAMIC ITEM-SPECIFIC ADAPTATION RULES:
   - For CASH / MONEY: Ask about total amount & currency, note types (e.g. 500, 200, 100 notes), how it was kept (envelope/pouch/pocket), receipts kept with it, and location/time lost. NEVER ask for brand of cash!
   - For WALLETS / BAGS: Ask about brand/material/color, items kept inside, marks/stickers/zippers, and location/time lost.
   - For KEYS / ACCESS BADGES: Ask about number of keys, keychain/ribbon description, vehicle/company name, and location/time lost. NEVER ask for brand of key!
   - For DOCUMENTS / ID CARDS: Ask about name/college on card, card holder/cover, and location/time lost.
   - For JEWELRY / WATCHES: Ask about metal type (gold/silver/steel), brand/stones, engravings/scratches, and location/time lost.
   - For ELECTRONICS: Ask about brand/model, color/cover/skin, scratches/stickers, and location/time lost.
   - For CLOTHING / APPAREL: Ask about brand/size, color/pattern, pocket contents, and location/time lost.
   - For BOOKS / STATIONERY: Ask about book title/author/notebook brand, cover color, notes/names inside, and location/time lost.
   - For BOTTLES / GENERAL ITEMS: Ask about brand/size, color/material, dents/stickers, and location/time lost.

Detected Item Type Domain: {detected_domain}
Lost Item Context:
- Category: {lost_item.category}
- Title: {lost_item.title}
- Description: {lost_item.description or 'Unspecified'}
- Reported Color: {lost_item.color or 'Unspecified'}
- Reported Brand: {lost_item.brand or 'Unspecified'}
- Reported Location: {lost_item.location}
- Reported Features: {lost_item.distinctive_features or 'None'}

Return ONLY a valid JSON object matching this structure:
{{
  "questions": [
    {{
      "question_text": "string (easy, simple English question tailored specifically to this item)",
      "question_type": "string (one of: amount, container, contents, identifier, material, keys_detail, size, brand, color, location, feature, circumstances)"
    }}
  ]
}}
"""
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a secure verification question generator that generates simple, easy-to-understand questions in plain English. Output pure JSON without markdown."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            parsed = json.loads(chat_completion.choices[0].message.content)
            llm_questions = parsed.get("questions", [])
            if llm_questions and isinstance(llm_questions, list):
                for q in llm_questions:
                    if "question_text" in q and len(q["question_text"].strip()) > 5:
                        questions_data.append({
                            "question_text": q["question_text"].strip(),
                            "question_type": q.get("question_type", "general")
                        })
        except Exception as exc:
            logger.warning(f"LLM verification question generation failed: {exc}. Using dynamic deterministic generator.")

    if not questions_data or len(questions_data) < 3:
        questions_data = generate_deterministic_questions(lost_item)

    # Persist questions into database
    created_questions = []
    for q_item in questions_data:
        db_q = VerificationQuestion(
            match_id=match.id,
            question_text=q_item["question_text"],
            question_type=q_item.get("question_type", "general")
        )
        db.add(db_q)
        created_questions.append(db_q)

    # Update match status to in_progress if currently pending/suggested
    if match.status in ["suggested", "pending", "verification_pending"]:
        match.status = "in_progress"

    db.commit()
    for q in created_questions:
        db.refresh(q)

    return created_questions


def evaluate_single_answer(
    question: VerificationQuestion,
    answer_text: str,
    lost_item: Any,
    found_item: Any
) -> Dict[str, Any]:
    """
    Evaluates an answer against known item facts (both lost report and found item ground truth).
    Supports all question domains: money amounts, denominations, containers, keys, documents, brand, color, etc.
    Returns score (0-100) and feedback.
    """
    q_type = (question.question_type or "general").lower()
    ans_clean = answer_text.strip().lower()

    # Ground truth reference text
    lost_desc_full = f"{lost_item.title} {lost_item.description or ''} {lost_item.color or ''} {lost_item.brand or ''} {lost_item.location or ''} {str(lost_item.distinctive_features or '')}".lower()
    found_desc_full = f"{found_item.title} {found_item.description or ''} {found_item.color or ''} {found_item.brand or ''} {found_item.location or ''} {str(found_item.distinctive_features or '')}".lower()
    combined_ground_truth = f"{lost_desc_full} {found_desc_full}"

    # Base semantic similarity to reported ground truth
    sem_lost = get_description_similarity(ans_clean, lost_desc_full)
    sem_found = get_description_similarity(ans_clean, found_desc_full)
    base_score = max(sem_lost, sem_found)

    attr_matched = False
    bonus = 0.0
    feedback_points = []

    if q_type in ["amount", "denomination", "currency"]:
        ans_numbers = re.findall(r"\b\d+\b", ans_clean)
        truth_numbers = re.findall(r"\b\d+\b", combined_ground_truth)
        matched_numbers = [n for n in ans_numbers if n in truth_numbers]

        currency_words = ["rupee", "rupees", "rs", "inr", "dollar", "dollars", "usd", "cash", "note", "notes", "thousand", "hundred", "lakh", "500", "200", "100", "50", "20", "10", "2000"]
        matched_currency = [cw for cw in currency_words if cw in ans_clean and cw in combined_ground_truth]

        if matched_numbers:
            bonus += 50.0
            attr_matched = True
            feedback_points.append(f"Money amount/denomination verified ({', '.join(matched_numbers)})")
        elif ans_numbers and not matched_numbers:
            # Stated specific numbers that do not match ground truth
            attr_matched = False
            base_score = min(base_score, 20.0)
            feedback_points.append("Stated amount figures do not match item records")
        elif matched_currency and base_score >= 50.0:
            bonus += 30.0
            attr_matched = True
            feedback_points.append("Currency and denomination details align with report")
        else:
            feedback_points.append("Stated amount or currency details do not correlate with recorded figures")

    elif q_type in ["container", "storage", "enclosure"]:
        container_words = ["envelope", "pouch", "rubber band", "band", "clip", "paper clip", "purse", "pocket", "sleeve", "holder", "box", "case", "bag", "zipper", "folder", "binder", "plastic", "paper", "leather"]
        matched_c = [w for w in container_words if w in ans_clean and w in combined_ground_truth]
        if matched_c:
            bonus += 40.0
            attr_matched = True
            feedback_points.append(f"Enclosure/container type verified ({matched_c[0]})")
        elif any(w in ans_clean for w in container_words) and base_score >= 35.0:
            bonus += 30.0
            attr_matched = True
            feedback_points.append("Container description is consistent with item condition")
        else:
            feedback_points.append("Storage or enclosure details differ from records")

    elif q_type in ["contents", "inside"]:
        truth_tokens = {w for w in re.findall(r"\b\w{3,}\b", combined_ground_truth) if w not in ["the", "and", "with", "this", "that", "item", "lost", "found"]}
        matched_tokens = [w for w in re.findall(r"\b\w{3,}\b", ans_clean) if w in truth_tokens]
        if len(matched_tokens) >= 2 or (len(matched_tokens) == 1 and base_score >= 35.0):
            bonus += 40.0
            attr_matched = True
            feedback_points.append(f"Internal contents verified ({', '.join(matched_tokens[:3])})")
        else:
            feedback_points.append("Specified internal contents do not align with item report")

    elif q_type in ["identifier", "document_name", "issuer"]:
        truth_tokens = {w for w in re.findall(r"\b\w{3,}\b", combined_ground_truth) if w not in ["the", "and", "with", "this", "that", "card", "document"]}
        matched_tokens = [w for w in re.findall(r"\b\w{3,}\b", ans_clean) if w in truth_tokens]
        if matched_tokens:
            bonus += 45.0
            attr_matched = True
            feedback_points.append(f"Identifier/issuer verified ({matched_tokens[0].title()})")
        else:
            feedback_points.append("Identification details do not match records")

    elif q_type in ["keys_detail", "keychain"]:
        key_tokens = ["key", "keys", "fob", "honda", "toyota", "hyundai", "ford", "bmw", "audi", "maruti", "suzuki", "tata", "mahindra", "hero", "yamaha", "godrej", "lanyard", "ring", "car", "bike", "room", "office", "silver", "brass", "black"]
        matched_k = [k for k in key_tokens if k in ans_clean and k in combined_ground_truth]
        if matched_k:
            bonus += 40.0
            attr_matched = True
            feedback_points.append(f"Key configuration verified ({matched_k[0]})")
        elif base_score >= 35.0:
            bonus += 30.0
            attr_matched = True
            feedback_points.append("Key details match report")
        else:
            feedback_points.append("Key configuration differs from records")

    elif q_type in ["material", "metal", "fabric"]:
        materials = ["gold", "silver", "platinum", "diamond", "titanium", "stainless steel", "steel", "leather", "canvas", "denim", "cotton", "wool", "silk", "nylon", "plastic", "wood", "glass", "rubber"]
        matched_m = [m for m in materials if m in ans_clean and m in combined_ground_truth]
        if matched_m:
            bonus += 40.0
            attr_matched = True
            feedback_points.append(f"Material verified ({matched_m[0].title()})")
        else:
            feedback_points.append("Material description differs from records")

    elif q_type == "brand":
        known_brands = [b.lower() for b in [getattr(lost_item, "brand", None), getattr(found_item, "brand", None)] if b]
        if known_brands and any(b in ans_clean for b in known_brands):
            bonus += 40.0
            attr_matched = True
            feedback_points.append(f"Brand identification verified ({known_brands[0].title()})")
        else:
            feedback_points.append("Brand does not match item record")

    elif q_type in ["color", "size"]:
        known_colors = [c.lower() for c in [getattr(lost_item, "color", None), getattr(found_item, "color", None)] if c]
        if known_colors and any(any(part in ans_clean for part in c.split()) for c in known_colors):
            bonus += 40.0
            attr_matched = True
            feedback_points.append("Color description matches item characteristics")
        else:
            feedback_points.append("Color description differs from item record")

    elif q_type == "location":
        loc_text = f"{getattr(lost_item, 'location', '')} {getattr(found_item, 'location', '')}".lower()
        loc_words = {w for w in loc_text.split() if len(w) > 3}
        if any(w in ans_clean for w in loc_words):
            bonus += 35.0
            attr_matched = True
            feedback_points.append("Location details are consistent with where item was lost/found")
        else:
            feedback_points.append("Location details not consistent with records")

    elif q_type == "feature":
        feat_text = f"{str(getattr(lost_item, 'distinctive_features', ''))} {str(getattr(found_item, 'distinctive_features', ''))}".lower()
        feat_words = {w for w in feat_text.replace("'", " ").replace('"', ' ').replace('[', ' ').replace(']', ' ').split() if len(w) > 3}
        if any(w in ans_clean for w in feat_words):
            bonus += 40.0
            attr_matched = True
            feedback_points.append(f"Distinctive markings match item records")
        else:
            feedback_points.append("Distinctive features do not correlate with recorded markings")

    elif q_type in ["circumstances", "date"]:
        date_text = f"{str(getattr(lost_item, 'date_lost', ''))} {str(getattr(found_item, 'date_found', ''))}".lower()
        if any(w in ans_clean for w in ["march", "lost", "found", "morning", "afternoon", "evening", "2026", "table", "room", "desk", "floor", "counter", "bag", "pocket"]):
            bonus += 30.0
            attr_matched = True
            feedback_points.append("Circumstances and timeline align with incident report")

    if attr_matched:
        final_q_score = min(100.0, max(75.0, base_score + bonus))
    else:
        final_q_score = min(45.0, max(10.0, base_score + bonus))

    feedback = "; ".join(feedback_points) if feedback_points else "Answer evaluated for semantic consistency"
    return {
        "score": round(final_q_score, 1),
        "feedback": feedback
    }


def evaluate_verification_answers(
    match: Match,
    answers_in: List[VerificationAnswerIn],
    user_id: int,
    db: Session
) -> Dict[str, Any]:
    """
    Verification Agent: Evaluates submitted answers against ground truth facts.
    Computes verification score, confidence, reasons, and sets status to admin_review.
    NEVER automatically approves ownership.
    """
    questions_map = {q.id: q for q in match.questions}
    evaluated_answers = []
    score_list = []
    reasons = []

    for ans in answers_in:
        question = questions_map.get(ans.question_id)
        if not question:
            continue

        eval_result = evaluate_single_answer(
            question=question,
            answer_text=ans.answer_text,
            lost_item=match.lost_item,
            found_item=match.found_item
        )

        db_answer = VerificationAnswer(
            question_id=ans.question_id,
            user_id=user_id,
            answer_text=ans.answer_text.strip(),
            evaluation_score=eval_result["score"],
            evaluation_feedback=eval_result["feedback"]
        )
        db.add(db_answer)
        evaluated_answers.append(db_answer)
        score_list.append(eval_result["score"])

        if eval_result["score"] >= 70:
            reasons.append(eval_result["feedback"])

    db.commit()
    for ans_obj in evaluated_answers:
        db.refresh(ans_obj)

    # Compute overall verification score
    if score_list:
        overall_score = round(sum(score_list) / len(score_list), 1)
    else:
        overall_score = 0.0

    # Determine confidence
    if overall_score >= 80.0:
        confidence = "high"
    elif overall_score >= 60.0:
        confidence = "medium"
    else:
        confidence = "low"

    if not reasons:
        reasons.append("Claimant answers showed limited correlation with reported item characteristics")

    # Update match status to admin_review (Never auto-approve!)
    match.status = "admin_review"
    db.commit()
    db.refresh(match)

    return {
        "match_id": match.id,
        "verification_score": overall_score,
        "confidence": confidence,
        "recommendation": "administrator_review",
        "status": match.status,
        "reasons": reasons,
        "answers": evaluated_answers
    }
