from __future__ import annotations

import math
import os
import re
from collections import Counter
from functools import lru_cache


def embedding_similarity(text_a: str, text_b: str) -> tuple[float, str]:
    provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()
    if provider == "sentence-transformers":
        score = _sentence_transformer_similarity(text_a, text_b)
        if score is not None:
            return score, "sentence-transformers"
    return _local_similarity(text_a, text_b), "local-token-cosine"


def _sentence_transformer_similarity(text_a: str, text_b: str) -> float | None:
    try:
        from sentence_transformers import SentenceTransformer
    except Exception:
        return None

    model = _load_sentence_model()
    vectors = model.encode([text_a, text_b], normalize_embeddings=True)
    return float(max(0, min(1, sum(float(a) * float(b) for a, b in zip(vectors[0], vectors[1])))))


@lru_cache(maxsize=1)
def _load_sentence_model():
    from sentence_transformers import SentenceTransformer

    model_name = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
    return SentenceTransformer(model_name)


def _local_similarity(text_a: str, text_b: str) -> float:
    a = _token_vector(text_a)
    b = _token_vector(text_b)
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    numerator = sum(a[token] * b[token] for token in common)
    a_norm = math.sqrt(sum(value * value for value in a.values()))
    b_norm = math.sqrt(sum(value * value for value in b.values()))
    if not a_norm or not b_norm:
        return 0.0
    return numerator / (a_norm * b_norm)


def _token_vector(text: str) -> Counter:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z+#.]{1,}", text.lower())
    stopwords = {"and", "the", "for", "with", "from", "this", "that", "have", "will", "need", "role"}
    return Counter(token for token in tokens if token not in stopwords)
