"""
Deterministic Normalization Engine.
Converts numbers, currencies, percentages, dates, periods, and units to canonical representations.
Zero LLM calls for arithmetic or deterministic string conversions.
"""

import re
from typing import Optional, Tuple, Dict, Any
from models.fact import Period

MULTIPLIERS = {
    "trillion": 1e12,
    "billion": 1e9,
    "bn": 1e9,
    "b": 1e9,
    "crore": 1e7,
    "crores": 1e7,
    "cr": 1e7,
    "cr.": 1e7,
    "million": 1e6,
    "mn": 1e6,
    "m": 1e6,
    "lakh": 1e5,
    "lakhs": 1e5,
    "lac": 1e5,
    "thousand": 1e3,
    "k": 1e3
}

CURRENCY_SYMBOLS = {
    "₹": "INR",
    "inr": "INR",
    "rs": "INR",
    "rs.": "INR",
    "rupees": "INR",
    "$": "USD",
    "usd": "USD",
    "dollar": "USD",
    "dollars": "USD",
    "€": "EUR",
    "eur": "EUR",
    "£": "GBP",
    "gbp": "GBP"
}

class Normalizer:
    """Normalizes raw numeric, currency, percentage, and period values."""

    @staticmethod
    def normalize_number(text: Any) -> Optional[float]:
        """Convert string representations like '8,142', '(2,492.34)', '8.14k' to float."""
        if text is None:
            return None
        if isinstance(text, (int, float)):
            return float(text)

        s = str(text).strip()
        # Handle parentheses for negative numbers e.g. (2,492.34)
        is_negative = False
        if s.startswith("(") and s.endswith(")"):
            is_negative = True
            s = s[1:-1].strip()
        elif s.startswith("-"):
            is_negative = True
            s = s[1:].strip()

        # Remove commas, currency symbols, percentage signs
        s_clean = re.sub(r"[₹$,\s%]", "", s)

        # Check for trailing multiplier like 'k', 'm', 'cr'
        multiplier = 1.0
        for unit_key, mult in sorted(MULTIPLIERS.items(), key=lambda x: -len(x[0])):
            pattern = rf"(?i)(?<=\d)\s*{re.escape(unit_key)}$"
            if re.search(pattern, s_clean):
                multiplier = mult
                s_clean = re.sub(pattern, "", s_clean)
                break

        # Match float/int
        match = re.search(r"[-+]?\d*\.?\d+", s_clean)
        if match:
            try:
                val = round(float(match.group()) * multiplier, 6)
                return -val if is_negative else val
            except ValueError:
                return None
        return None

    @staticmethod
    def normalize_currency_and_value(raw_text: str, raw_val: Optional[float] = None, raw_unit: Optional[str] = None) -> Tuple[Optional[float], Optional[str], Optional[str]]:
        """
        Normalize currency amounts to canonical base units (e.g. base INR or USD).
        Returns: (canonical_value, canonical_currency, original_unit_canonical)
        """
        text = f"{raw_text} {raw_unit or ''}".lower()

        # Detect currency
        currency = None
        for sym, curr in CURRENCY_SYMBOLS.items():
            if sym in text:
                currency = curr
                break

        # Determine multiplier
        multiplier = 1.0
        unit_canonical = "unit"
        for unit_key, mult in sorted(MULTIPLIERS.items(), key=lambda x: -len(x[0])):
            if re.search(rf"\b{re.escape(unit_key)}\b", text):
                multiplier = mult
                unit_canonical = unit_key
                break

        num_val = raw_val if raw_val is not None else Normalizer.normalize_number(raw_text)
        if num_val is None:
            return None, currency, unit_canonical

        canonical_val = num_val * multiplier if multiplier > 1.0 else num_val
        return canonical_val, currency, (currency or unit_canonical)

    @staticmethod
    def normalize_percentage(text: Any) -> Optional[float]:
        """Convert '6.5%', '6.5 percent', '6.5 per cent' to float 6.5."""
        if text is None:
            return None
        if isinstance(text, (int, float)):
            return float(text)
        s = str(text).strip()
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent|per\s*cent)", s, re.IGNORECASE)
        if match:
            return float(match.group(1))
        # fallback to plain number if % context is in prompt
        num = Normalizer.normalize_number(s)
        return num

    @staticmethod
    def normalize_period(raw_period: Optional[str]) -> Optional[Period]:
        """
        Normalize diverse period representations:
        - FY24, FY 2023-24, FY2023/24, 2023-24 -> FY2023/24
        - Q1 FY25, Q1 2024-25 -> Q1 FY2024/25
        - 2024, CY2024 -> CY2024
        """
        if not raw_period:
            return None

        s = raw_period.strip()

        # Quarter Fiscal Year: Q1 FY25, Q4 FY24, Q1:2024-25, Q1 2024-25
        q_match = re.search(r"Q([1-4])(?:\s*[:/]\s*|\s+FY|\s+)?\s*(?:20)?(\d{2})(?:[-/](\d{2}))?", s, re.IGNORECASE)
        if q_match:
            quarter = int(q_match.group(1))
            raw_y = q_match.group(2)
            y2 = int("20" + raw_y)
            y1 = y2 - 1
            
            # Quarters in Indian Fiscal Year (April 1 - March 31)
            # Q1: Apr-Jun (y1), Q2: Jul-Sep (y1), Q3: Oct-Dec (y1), Q4: Jan-Mar (y2)
            q_bounds = {
                1: (f"{y1}-04-01", f"{y1}-06-30"),
                2: (f"{y1}-07-01", f"{y1}-09-30"),
                3: (f"{y1}-10-01", f"{y1}-12-31"),
                4: (f"{y2}-01-01", f"{y2}-03-31")
            }
            start_d, end_d = q_bounds[quarter]
            return Period(
                label=f"Q{quarter} FY{y1}/{str(y2)[-2:]}",
                period_type="quarter",
                start_date=start_d,
                end_date=end_d
            )

        # Fiscal Year with 4 digits: FY 2023-24, FY2023/24, 2023-24
        fy_match = re.search(r"(?:FY\s*)?20(\d{2})[-/](\d{2})", s, re.IGNORECASE)
        if fy_match:
            y1 = int("20" + fy_match.group(1))
            y2 = int("20" + fy_match.group(2))
            return Period(
                label=f"FY{y1}/{str(y2)[-2:]}",
                period_type="fiscal_year",
                start_date=f"{y1}-04-01",
                end_date=f"{y2}-03-31"
            )

        # Fiscal Year with 2 digits: FY24, FY 24, FY-24 (make sure no Q before it)
        fy_short = re.search(r"(?<![Qq]\d\s)\bFY\s*[-']?(\d{2})\b", s, re.IGNORECASE)
        if fy_short:
            y2 = int("20" + fy_short.group(1))
            y1 = y2 - 1
            return Period(
                label=f"FY{y1}/{str(y2)[-2:]}",
                period_type="fiscal_year",
                start_date=f"{y1}-04-01",
                end_date=f"{y2}-03-31"
            )

        # Calendar year: 2024, CY2024
        cy_match = re.search(r"\b(?:CY\s*)?(20\d{2})\b", s, re.IGNORECASE)
        if cy_match:
            year = cy_match.group(1)
            return Period(
                label=f"CY{year}",
                period_type="calendar_year",
                start_date=f"{year}-01-01",
                end_date=f"{year}-12-31"
            )

        return Period(
            label=s,
            period_type="unknown"
        )
