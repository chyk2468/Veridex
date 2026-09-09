"""
Candidate Fact Detector.
Filters and ranks evidence blocks containing quantitative or high-relevance semantic claims
to minimize LLM token consumption while ensuring full recall of critical disclosures.
"""

import re
from typing import List, Dict, Any
from models.evidence import Evidence

# High-salience patterns for numbers, currencies, percentages, and corporate metrics
FACT_PATTERNS = [
    r"[₹$€£]\s*[\d,]+(?:\.\d+)?",                                 # Currency symbols
    r"\b[\d,]+(?:\.\d+)?\s*(?:crore|lakh|million|billion|trillion|cr|mn|bn)\b", # Multipliers
    r"\b\d+(?:\.\d+)?\s*(?:%|percent|per\s*cent)\b",             # Percentages
    r"\b(?:FY\s*[-']?\d{2,4}|20\d{2}[-/]\d{2}|Q[1-4]\s*(?:FY|:|-)?\s*\d{2,4})\b", # Financial periods
    r"\b(?:revenue|ebitda|profit|loss|turnover|income|spend|expenditure)\b", # Financial metrics
    r"\b(?:real\s+GDP|inflation|deficit|repo\s+rate|forex|reserves)\b", # Macroeconomic metrics
    r"\b(?:pin\s*codes?|shipments?|facilities|centers|tonnage|volume)\b", # Operational metrics
    r"\b(?:director|managing\s+director|ceo|cto|cfo|compliance\s+officer|registered\s+office)\b" # Governance
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in FACT_PATTERNS]

class CandidateDetector:
    """Evaluates whether an evidence block is a candidate for fact extraction."""

    @staticmethod
    def is_candidate(text: str) -> bool:
        """Return True if text contains numbers, currencies, percentages, or key domain terms."""
        if not text or len(text.strip()) < 3:
            return False
        
        # Fast regex scan
        for pattern in COMPILED_PATTERNS:
            if pattern.search(text):
                return True
        return False

    @staticmethod
    def filter_candidate_evidence(evidence_list: List[Evidence]) -> List[Evidence]:
        """Filter a list of evidence items to retain only plausible candidates."""
        candidates = []
        for ev in evidence_list:
            if ev.evidence_type == "table" or CandidateDetector.is_candidate(ev.text):
                candidates.append(ev)
        return candidates
