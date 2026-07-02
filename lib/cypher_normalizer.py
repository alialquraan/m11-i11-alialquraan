"""Cypher normalization for the NL -> Cypher exact-match harness.

Per the integration spec methodology paragraph (NL -> Cypher exact-match):
collapse whitespace, strip leading/trailing whitespace, then case-insensitively
uppercase the seven Cypher keywords (MATCH, RETURN, WHERE, OPTIONAL, WITH,
LIMIT, ORDER BY). After normalization, two strings are exact-match iff they
are byte-equal.

The split between this module and eval_kg.py exists so the normalization logic
is unit-testable without a live backend.
"""
import re

KEYWORDS = (
    "MATCH",
    "RETURN",
    "WHERE",
    "OPTIONAL",
    "WITH",
    "LIMIT",
    "ORDER BY",
)


def normalize_cypher(s: str) -> str:
    """Return `s` normalized per the integration spec methodology: whitespace
    collapse and keyword uppercasing. See the module docstring for the full
    methodology paragraph.
    """
    # 1. Collapse whitespace and strip
    s_clean = re.sub(r"\s+", " ", s).strip()
    
    # 2. Case-insensitively uppercase the seven keywords
    # نرتب الكلمات بحيث يتم معالجة "ORDER BY" قبل "ORDER" (إن وُجدت مستقبلاً) منعاً للتداخل
    for kw in KEYWORDS:
        pattern = r"\b" + re.escape(kw).replace(r"\ ", r"\s+") + r"\b"
        s_clean = re.sub(pattern, kw, s_clean, flags=re.IGNORECASE)
        
    return s_clean