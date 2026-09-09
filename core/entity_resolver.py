"""
Entity Resolution Engine.
Conservatively resolves entity aliases and metric predicates without over-merging ambiguous entities.
Computes interpretable entity_match_confidence scores.
"""

import re
from typing import Tuple, Dict, Any, Optional

CANONICAL_ENTITIES: Dict[str, str] = {
    "delhivery": "Delhivery Limited",
    "delhivery limited": "Delhivery Limited",
    "delhivery ltd": "Delhivery Limited",
    "delhivery ltd.": "Delhivery Limited",
    "the company": "Delhivery Limited",
    "our company": "Delhivery Limited",
    "india": "India",
    "republic of india": "India",
    "government of india": "India",
    "goi": "India",
    "reserve bank of india": "Reserve Bank of India",
    "rbi": "Reserve Bank of India",
    "international monetary fund": "International Monetary Fund",
    "imf": "International Monetary Fund"
}

CANONICAL_PREDICATES: Dict[str, str] = {
    "revenue from operations": "revenue from operations",
    "consolidated revenue": "revenue from operations",
    "total revenue from operations": "revenue from operations",
    "revenue": "revenue from operations",
    "turnover": "revenue from operations",
    "real gdp growth": "real GDP growth",
    "real gdp growth rate": "real GDP growth",
    "growth in real gdp": "real GDP growth",
    "economic growth": "real GDP growth",
    "cpi inflation": "headline CPI inflation",
    "headline cpi inflation": "headline CPI inflation",
    "headline inflation": "headline CPI inflation",
    "cpi headline inflation": "headline CPI inflation",
    "pin code reach": "pin codes covered",
    "pin codes covered": "pin codes covered",
    "pin-code reach": "pin codes covered",
    "pin-codes covered": "pin codes covered",
    "total pin codes": "total pin codes in india",
    "pin codes in india": "total pin codes in india"
}

LEGAL_SUFFIXES = [
    r"\blimited\b", r"\bltd\.?\b", r"\bprivate\b", r"\bpvt\.?\b",
    r"\bincorporated\b", r"\binc\.?\b", r"\bcorporation\b", r"\bcorp\.?\b"
]

class EntityResolver:
    """Resolves and normalizes entities and predicates with explicit confidence scores."""

    @staticmethod
    def clean_name(name: str) -> str:
        s = name.strip().lower()
        s = re.sub(r"[^\w\s]", "", s)
        return re.sub(r"\s+", " ", s).strip()

    @staticmethod
    def strip_legal_suffixes(name: str) -> str:
        s = name.strip()
        for suffix in LEGAL_SUFFIXES:
            s = re.sub(suffix, "", s, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", s).strip()

    @classmethod
    def resolve_entity(cls, raw_entity: str) -> Tuple[str, float]:
        """
        Normalize entity name to canonical form.
        Returns: (canonical_entity, match_confidence)
        """
        if not raw_entity or not raw_entity.strip():
            return "Unknown Entity", 0.0

        cleaned = cls.clean_name(raw_entity)
        if cleaned in CANONICAL_ENTITIES:
            return CANONICAL_ENTITIES[cleaned], 1.0

        stripped = cls.clean_name(cls.strip_legal_suffixes(raw_entity))
        if stripped in CANONICAL_ENTITIES:
            return CANONICAL_ENTITIES[stripped], 0.95

        # Return original with proper capitalization if unrecognized
        return raw_entity.strip(), 0.70

    @classmethod
    def resolve_predicate(cls, raw_predicate: str) -> Tuple[str, float]:
        """
        Normalize predicate / metric to canonical form.
        Returns: (canonical_predicate, match_confidence)
        """
        if not raw_predicate or not raw_predicate.strip():
            return "unknown metric", 0.0

        cleaned = cls.clean_name(raw_predicate)
        if cleaned in CANONICAL_PREDICATES:
            return CANONICAL_PREDICATES[cleaned], 1.0

        # Partial substring match
        for key, canonical in CANONICAL_PREDICATES.items():
            if key in cleaned or cleaned in key:
                return canonical, 0.85

        return raw_predicate.strip().lower(), 0.65

    @classmethod
    def match_entities(cls, ent_a: str, ent_b: str) -> Tuple[bool, float]:
        """
        Compare two entity strings.
        Returns: (is_match, similarity_score)
        """
        canon_a, conf_a = cls.resolve_entity(ent_a)
        canon_b, conf_b = cls.resolve_entity(ent_b)

        if canon_a.lower() == canon_b.lower() and canon_a != "Unknown Entity":
            return True, min(conf_a, conf_b)

        # Lexical token overlap
        tokens_a = set(cls.clean_name(ent_a).split())
        tokens_b = set(cls.clean_name(ent_b).split())
        if not tokens_a or not tokens_b:
            return False, 0.0

        intersection = tokens_a.intersection(tokens_b)
        union = tokens_a.union(tokens_b)
        jaccard = len(intersection) / len(union)

        if jaccard >= 0.75:
            return True, round(jaccard, 2)

        return False, round(jaccard, 2)

    @classmethod
    def match_predicates(cls, pred_a: str, pred_b: str) -> Tuple[bool, float]:
        """
        Compare two predicate strings.
        Returns: (is_match, similarity_score)
        """
        canon_a, conf_a = cls.resolve_predicate(pred_a)
        canon_b, conf_b = cls.resolve_predicate(pred_b)

        if canon_a.lower() == canon_b.lower() and canon_a != "unknown metric":
            return True, min(conf_a, conf_b)

        tokens_a = set(cls.clean_name(pred_a).split())
        tokens_b = set(cls.clean_name(pred_b).split())
        if not tokens_a or not tokens_b:
            return False, 0.0

        intersection = tokens_a.intersection(tokens_b)
        union = tokens_a.union(tokens_b)
        jaccard = len(intersection) / len(union)

        if jaccard >= 0.60:
            return True, round(jaccard, 2)

        return False, round(jaccard, 2)
