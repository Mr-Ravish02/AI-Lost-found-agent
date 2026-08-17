import logging
import numpy as np
from typing import List, Union, Optional

logger = logging.getLogger(__name__)

# Global model instance for singleton reuse across requests
_model_instance = None
_model_failed = False
_embedding_cache = {}


def get_embedding_model():
    """Lazy load SentenceTransformer model (all-MiniLM-L6-v2) with fast local fallback."""
    global _model_instance, _model_failed
    if _model_instance is not None:
        return _model_instance
    if _model_failed:
        return None

    try:
        import os
        from sentence_transformers import SentenceTransformer
        try:
            _model_instance = SentenceTransformer('all-MiniLM-L6-v2', local_files_only=True)
        except Exception:
            # If not in local cache, fallback immediately to fast token/lexical similarity
            logger.info("SentenceTransformer not in local cache. Using fast lexical & token similarity.")
            _model_failed = True
            return None
        return _model_instance
    except Exception as exc:
        logger.warning(f"SentenceTransformer not available: {exc}. Using fast lexical & token similarity.")
        _model_failed = True
        return None


def get_text_embedding(text: str) -> Optional[np.ndarray]:
    """Generates a normalized embedding vector for a given text string."""
    if not text or not text.strip():
        return None

    text_clean = text.strip()
    if text_clean in _embedding_cache:
        return _embedding_cache[text_clean]

    model = get_embedding_model()
    if model is not None:
        try:
            emb = model.encode(text_clean, convert_to_numpy=True, normalize_embeddings=True)
            _embedding_cache[text_clean] = emb
            return emb
        except Exception as exc:
            logger.warning(f"Embedding generation error: {exc}")

    return None


def compute_cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Calculates cosine similarity between two numpy vectors, returning float in range [0.0, 1.0]."""
    if vec_a is None or vec_b is None:
        return 0.0
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    sim = float(np.dot(vec_a, vec_b) / (norm_a * norm_b))
    # Bound between 0.0 and 1.0
    return max(0.0, min(1.0, (sim + 1.0) / 2.0 if sim < 0 else sim))


def fallback_text_similarity(text1: str, text2: str) -> float:
    """Token/n-gram Jaccard & Levenshtein similarity fallback when neural model is unavailable."""
    if not text1 or not text2:
        return 0.0
    
    t1 = text1.lower().strip()
    t2 = text2.lower().strip()
    
    if t1 == t2:
        return 1.0

    # Word-level Jaccard similarity
    words1 = set(t1.split())
    words2 = set(t2.split())
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    jaccard = intersection / union if union > 0 else 0.0

    # Substring containment check
    containment = 0.0
    if t1 in t2 or t2 in t1:
        containment = 0.85

    # Levenshtein ratio if available
    lev_ratio = 0.0
    try:
        from RapidFuzz import fuzz
        lev_ratio = fuzz.token_sort_ratio(t1, t2) / 100.0
    except ImportError:
        try:
            from fuzzywuzzy import fuzz
            lev_ratio = fuzz.token_sort_ratio(t1, t2) / 100.0
        except ImportError:
            pass

    return max(jaccard, containment, lev_ratio)


def get_description_similarity(text1: str, text2: str) -> float:
    """Main interface to get semantic similarity between two descriptions (0.0 to 100.0)."""
    if not text1 or not text2:
        return 0.0
    
    vec1 = get_text_embedding(text1)
    vec2 = get_text_embedding(text2)
    
    if vec1 is not None and vec2 is not None:
        cos_sim = compute_cosine_similarity(vec1, vec2)
        return round(cos_sim * 100.0, 2)
    
    # Fallback to lexical/token similarity
    sim = fallback_text_similarity(text1, text2)
    return round(sim * 100.0, 2)
