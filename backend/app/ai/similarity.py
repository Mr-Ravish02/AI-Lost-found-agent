import datetime
from typing import Dict, Any, List, Optional, Union
from app.ai.embeddings import get_description_similarity

# Default Factor Weights (Sum = 100)
DEFAULT_WEIGHTS = {
    "text": 30.0,
    "category": 15.0,
    "location": 15.0,
    "color": 10.0,
    "brand": 10.0,
    "date": 10.0,
    "features": 10.0,
}

# Confidence Thresholds
CONFIDENCE_HIGH_THRESHOLD = 80.0
CONFIDENCE_MEDIUM_THRESHOLD = 60.0


def score_text_similarity(desc1: Optional[str], desc2: Optional[str]) -> Optional[float]:
    """Calculates semantic similarity between descriptions."""
    if not desc1 or not desc2 or not desc1.strip() or not desc2.strip():
        return None
    return get_description_similarity(desc1, desc2)


def score_category_similarity(cat1: Optional[str], cat2: Optional[str]) -> float:
    """Evaluates category match."""
    if not cat1 or not cat2:
        return 50.0  # neutral if unknown
    c1 = cat1.strip().lower()
    c2 = cat2.strip().lower()
    if c1 == c2:
        return 100.0
    if c1 in c2 or c2 in c1:
        return 80.0
    return 0.0


def score_color_similarity(col1: Optional[str], col2: Optional[str]) -> Optional[float]:
    """Evaluates color similarity. Returns None if either is missing for dynamic weighting."""
    if not col1 or not col2 or not col1.strip() or not col2.strip():
        return None
    
    c1_words = set(col1.lower().replace('/', ' ').replace(',', ' ').split())
    c2_words = set(col2.lower().replace('/', ' ').replace(',', ' ').split())
    
    if not c1_words or not c2_words:
        return None
    
    overlap = c1_words.intersection(c2_words)
    if overlap:
        return 100.0
    
    # Check partial substring
    for w1 in c1_words:
        for w2 in c2_words:
            if w1 in w2 or w2 in w1:
                return 80.0
    
    return 0.0


def score_brand_similarity(brand1: Optional[str], brand2: Optional[str]) -> Optional[float]:
    """Evaluates brand/maker match. Returns None if either missing."""
    if not brand1 or not brand2 or not brand1.strip() or not brand2.strip():
        return None
    
    b1 = brand1.strip().lower()
    b2 = brand2.strip().lower()
    
    if b1 == b2:
        return 100.0
    if b1 in b2 or b2 in b1:
        return 85.0
    return 0.0


def score_location_similarity(loc1: Optional[str], loc2: Optional[str]) -> float:
    """Evaluates location proximity / textual similarity."""
    if not loc1 or not loc2 or not loc1.strip() or not loc2.strip():
        return 50.0
    
    l1 = loc1.strip().lower()
    l2 = loc2.strip().lower()
    
    if l1 == l2:
        return 100.0
    
    # Check word intersection
    stop_words = {"in", "at", "near", "on", "the", "floor", "room", "building", "hall", "block"}
    words1 = {w for w in l1.replace(',', ' ').replace('-', ' ').split() if w not in stop_words and len(w) > 2}
    words2 = {w for w in l2.replace(',', ' ').replace('-', ' ').split() if w not in stop_words and len(w) > 2}
    
    if words1 and words2:
        common = words1.intersection(words2)
        if common:
            ratio = len(common) / max(len(words1), len(words2))
            return min(100.0, 70.0 + ratio * 30.0)
    
    if l1 in l2 or l2 in l1:
        return 85.0

    return 20.0


def score_date_proximity(date1_str: Optional[str], date2_str: Optional[str]) -> Optional[float]:
    """Evaluates temporal proximity between report dates (YYYY-MM-DD)."""
    if not date1_str or not date2_str:
        return None
    
    try:
        # Extract YYYY-MM-DD if timestamp
        d1_clean = date1_str.split('T')[0].split(' ')[0]
        d2_clean = date2_str.split('T')[0].split(' ')[0]
        
        d1 = datetime.date.fromisoformat(d1_clean)
        d2 = datetime.date.fromisoformat(d2_clean)
        
        days_diff = abs((d1 - d2).days)
        
        if days_diff == 0:
            return 100.0
        elif days_diff <= 2:
            return 90.0
        elif days_diff <= 5:
            return 80.0
        elif days_diff <= 10:
            return 65.0
        elif days_diff <= 20:
            return 45.0
        elif days_diff <= 35:
            return 25.0
        else:
            return 10.0
    except Exception:
        return None


def score_distinctive_features(
    feat1: Optional[Union[List[str], str]], 
    feat2: Optional[Union[List[str], str]]
) -> Optional[float]:
    """Evaluates distinctive features overlap."""
    if not feat1 or not feat2:
        return None
    
    # Normalize to list of strings
    list1 = feat1 if isinstance(feat1, list) else [str(feat1)]
    list2 = feat2 if isinstance(feat2, list) else [str(feat2)]
    
    list1 = [f.strip().lower() for f in list1 if f and f.strip()]
    list2 = [f.strip().lower() for f in list2 if f and f.strip()]
    
    if not list1 or not list2:
        return None
    
    max_sim = 0.0
    for f1 in list1:
        for f2 in list2:
            if f1 == f2:
                max_sim = max(max_sim, 100.0)
            elif f1 in f2 or f2 in f1:
                max_sim = max(max_sim, 85.0)
            else:
                sem = get_description_similarity(f1, f2)
                max_sim = max(max_sim, sem)
    
    return round(max_sim, 2)


def calculate_match_similarity(lost_item_dict: Dict[str, Any], found_item_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main Similarity Engine combining multi-factor scoring with dynamic weight normalization.
    Returns:
    {
      "final_score": float (0.0 to 100.0),
      "confidence": "high" | "medium" | "low",
      "factors": { "text": float, "category": float, ... },
      "reasons": list of strings
    }
    """
    # 1. Compute individual factor scores
    raw_scores = {
        "text": score_text_similarity(
            f"{lost_item_dict.get('title', '')} {lost_item_dict.get('description', '')}",
            f"{found_item_dict.get('title', '')} {found_item_dict.get('description', '')}"
        ),
        "category": score_category_similarity(
            lost_item_dict.get('category'),
            found_item_dict.get('category')
        ),
        "location": score_location_similarity(
            lost_item_dict.get('location'),
            found_item_dict.get('location')
        ),
        "color": score_color_similarity(
            lost_item_dict.get('color'),
            found_item_dict.get('color')
        ),
        "brand": score_brand_similarity(
            lost_item_dict.get('brand'),
            found_item_dict.get('brand')
        ),
        "date": score_date_proximity(
            lost_item_dict.get('date_lost'),
            found_item_dict.get('date_found')
        ),
        "features": score_distinctive_features(
            lost_item_dict.get('distinctive_features'),
            found_item_dict.get('distinctive_features')
        ),
    }

    # 2. Dynamic weight normalization for available factors
    available_weight_sum = 0.0
    weighted_score_sum = 0.0
    factors_result = {}
    reasons = []

    for factor, score in raw_scores.items():
        if score is not None:
            weight = DEFAULT_WEIGHTS.get(factor, 10.0)
            available_weight_sum += weight
            weighted_score_sum += (score * weight)
            factors_result[factor] = round(score, 1)
        else:
            factors_result[factor] = None

    # Calculate final normalized score
    if available_weight_sum > 0:
        final_score = round(weighted_score_sum / available_weight_sum, 1)
    else:
        final_score = 0.0

    # Ensure bounds [0.0, 100.0]
    final_score = max(0.0, min(100.0, final_score))

    # Determine confidence tier
    if final_score >= CONFIDENCE_HIGH_THRESHOLD:
        confidence = "high"
    elif final_score >= CONFIDENCE_MEDIUM_THRESHOLD:
        confidence = "medium"
    else:
        confidence = "low"

    # 3. Generate human-readable reasons
    if factors_result.get("category", 0) >= 80:
        reasons.append("Matching item category")
    elif factors_result.get("category", 0) == 0:
        reasons.append("Different category")

    if factors_result.get("brand") is not None:
        if factors_result["brand"] >= 85:
            reasons.append(f"Same brand ({lost_item_dict.get('brand') or found_item_dict.get('brand')})")
        elif factors_result["brand"] == 0:
            reasons.append("Different brand")

    if factors_result.get("color") is not None and factors_result["color"] >= 80:
        reasons.append(f"Matching color ({lost_item_dict.get('color') or found_item_dict.get('color')})")

    if factors_result.get("location", 0) >= 70:
        reasons.append("Close or overlapping location")

    if factors_result.get("date") is not None and factors_result["date"] >= 80:
        reasons.append("Report dates are within close timeframe")

    if factors_result.get("features") is not None and factors_result["features"] >= 75:
        reasons.append("Similar distinctive features or identifiers")

    if factors_result.get("text", 0) >= 75:
        reasons.append("Strong description semantic alignment")

    if not reasons:
        reasons.append("Low overall factor correlation")

    return {
        "final_score": final_score,
        "confidence": confidence,
        "factors": factors_result,
        "reasons": reasons
    }
