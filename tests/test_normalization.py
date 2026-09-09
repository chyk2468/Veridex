"""
Unit tests for Deterministic Normalizer.
"""

import pytest
from core.normalizer import Normalizer

def test_number_normalization():
    assert Normalizer.normalize_number("8,142") == 8142.0
    assert Normalizer.normalize_number("8142") == 8142.0
    assert Normalizer.normalize_number("8.142k") == 8142.0
    assert Normalizer.normalize_number("(2,492.34)") == -2492.34
    assert Normalizer.normalize_number("-500") == -500.0

def test_currency_and_multiplier_normalization():
    # Crores
    c1, curr1, u1 = Normalizer.normalize_currency_and_value("₹8,142 Cr", 8142, "Cr")
    assert c1 == 81420000000.0
    assert curr1 == "INR"

    # Millions
    c2, curr2, u2 = Normalizer.normalize_currency_and_value("₹ 81,415.38 million", 81415.38, "million")
    assert c2 == 81415380000.0
    assert curr2 == "INR"

    # Relative difference between reported figures
    diff_pct = abs(c1 - c2) / c2 * 100
    assert diff_pct < 0.01  # less than 0.01% rounding difference

def test_percentage_normalization():
    assert Normalizer.normalize_percentage("6.5%") == 6.5
    assert Normalizer.normalize_percentage("6.5 percent") == 6.5
    assert Normalizer.normalize_percentage("6.4 per cent") == 6.4

def test_period_normalization():
    per_fy24 = Normalizer.normalize_period("FY24")
    assert per_fy24.label == "FY2023/24"
    assert per_fy24.start_date == "2023-04-01"
    assert per_fy24.end_date == "2024-03-31"

    per_full = Normalizer.normalize_period("FY 2023-24")
    assert per_fy24.is_exact_match(per_full)

    per_q1 = Normalizer.normalize_period("Q1 FY25")
    assert per_q1.period_type == "quarter"
    assert per_q1.start_date == "2024-04-01"
    assert per_q1.end_date == "2024-06-30"

    assert not per_fy24.overlaps(per_q1)
