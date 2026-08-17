import os
import json
import re
import logging
from typing import Dict, Any, Optional, List
from app.config import settings

logger = logging.getLogger(__name__)

# Common entity dictionaries for fallback rule-based extraction
KNOWN_COLORS = {
    "black", "white", "silver", "grey", "gray", "red", "blue", "navy", 
    "green", "yellow", "gold", "rose gold", "brown", "pink", "purple", "orange"
}

KNOWN_BRANDS = {
    "apple", "dell", "hp", "lenovo", "asus", "acer", "samsung", "sony",
    "fossil", "nike", "adidas", "puma", "casio", "bose", "beats", "jbl", "sandisk",
    "logitech", "anker", "boat", "oneplus", "google", "xiaomi", "realme", "jansport"
}

CATEGORIES_MAP = {
    "laptop": "Electronics",
    "notebook": "Electronics",
    "macbook": "Electronics",
    "phone": "Electronics",
    "iphone": "Electronics",
    "headphone": "Electronics",
    "headphones": "Electronics",
    "earbuds": "Electronics",
    "airpods": "Electronics",
    "charger": "Electronics",
    "wallet": "Wallets & Bags",
    "purse": "Wallets & Bags",
    "bag": "Wallets & Bags",
    "backpack": "Wallets & Bags",
    "key": "Keys & Badges",
    "keys": "Keys & Badges",
    "id": "Documents & Cards",
    "card": "Documents & Cards",
    "watch": "Accessories & Jewelry",
    "glasses": "Accessories & Jewelry",
    "jacket": "Clothing & Apparel",
    "bottle": "Other"
}


def rule_based_extract(text: str, existing_category: Optional[str] = None) -> Dict[str, Any]:
    """Fallback extraction using NLP regex and dictionary pattern matching."""
    text_lower = text.lower()

    # 1. Extract Color (sorted by text appearance)
    color_matches = []
    for color in KNOWN_COLORS:
        for m in re.finditer(r'\b' + re.escape(color) + r'\b', text_lower):
            color_matches.append((m.start(), color))
    color_matches.sort(key=lambda x: x[0])
    extracted_color = color_matches[0][1].title() if color_matches else None

    # 2. Extract Brand (sorted by text appearance)
    brand_matches = []
    for brand in KNOWN_BRANDS:
        for m in re.finditer(r'\b' + re.escape(brand) + r'\b', text_lower):
            brand_matches.append((m.start(), brand))
    brand_matches.sort(key=lambda x: x[0])
    extracted_brand = brand_matches[0][1].title() if brand_matches else None

    # 3. Extract Category
    category = existing_category
    if not category:
        for kw, cat in CATEGORIES_MAP.items():
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                category = cat
                break
        if not category:
            category = "Other"

    # 4. Extract Distinctive Features (stickers, scratches, marks, engravings, keychains)
    features = []
    sticker_match = re.findall(r'(?:with|has|a)\s+([^,.]*?sticker[^,.]*)', text_lower)
    features.extend([s.strip() for s in sticker_match if len(s.strip()) > 3])

    scratch_match = re.findall(r'([^,.]*?scratch[^,.]*)', text_lower)
    features.extend([s.strip() for s in scratch_match if len(s.strip()) > 3])

    keychain_match = re.findall(r'([^,.]*?keychain[^,.]*)', text_lower)
    features.extend([k.strip() for k in keychain_match if len(k.strip()) > 3])

    return {
        "category": category,
        "color": extracted_color,
        "brand": extracted_brand,
        "model": None,
        "location": None,
        "distinctive_features": features if features else None
    }


def extract_item_attributes(
    title: str,
    description: str,
    category: Optional[str] = None,
    color: Optional[str] = None,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    location: Optional[str] = None,
    distinctive_features: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Information Extraction Agent: Takes an item's raw text and metadata,
    then leverages Groq LLM (or robust local NLP fallback) to extract normalized structured data.
    """
    full_text = f"Title: {title}\nCategory: {category or ''}\nDescription: {description}\nLocation: {location or ''}\nExisting Color: {color or ''}\nExisting Brand: {brand or ''}\nExisting Features: {distinctive_features or ''}"

    # Check if Groq LLM is configured
    groq_api_key = settings.GROQ_API_KEY
    if groq_api_key and groq_api_key.strip() and not groq_api_key.startswith("your_"):
        try:
            from groq import Groq
            client = Groq(api_key=groq_api_key)

            prompt = f"""You are an Information Extraction Agent for a Lost and Found system.
Extract normalized structured JSON from the following item report.
Return ONLY valid JSON matching this exact structure:
{{
  "category": "string (e.g. Electronics, Wallets & Bags, Keys & Badges, Documents & Cards, Other)",
  "color": "string or null",
  "brand": "string or null",
  "model": "string or null",
  "location": "string or null",
  "distinctive_features": ["list of strings (identifying marks, stickers, engravings)"]
}}

Item Report:
{full_text}
"""
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a precise data extraction agent. Output pure JSON without markdown code blocks."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = chat_completion.choices[0].message.content
            parsed = json.loads(content)
            
            # Merge with existing explicit fields if LLM missed them
            return {
                "category": parsed.get("category") or category or "Other",
                "color": parsed.get("color") or color,
                "brand": parsed.get("brand") or brand,
                "model": parsed.get("model") or model,
                "location": parsed.get("location") or location,
                "distinctive_features": parsed.get("distinctive_features") or distinctive_features or []
            }
        except Exception as exc:
            logger.warning(f"Groq Extraction failed: {exc}. Using rule-based fallback.")

    # Fallback mode
    extracted = rule_based_extract(f"{title} {description}", existing_category=category)
    return {
        "category": category or extracted.get("category"),
        "color": color or extracted.get("color"),
        "brand": brand or extracted.get("brand"),
        "model": model or extracted.get("model"),
        "location": location or extracted.get("location"),
        "distinctive_features": distinctive_features or extracted.get("distinctive_features") or []
    }
