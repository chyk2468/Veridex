"""
Unit tests for Entity Resolution.
"""

import pytest
from core.entity_resolver import EntityResolver

def test_entity_canonicalization():
    name, conf = EntityResolver.resolve_entity("Delhivery Limited")
    assert name == "Delhivery Limited"
    assert conf == 1.0

    name2, conf2 = EntityResolver.resolve_entity("Delhivery Ltd.")
    assert name2 == "Delhivery Limited"
    assert conf2 >= 0.95

    name3, conf3 = EntityResolver.resolve_entity("Republic of India")
    assert name3 == "India"
    assert conf3 == 1.0

def test_entity_matching():
    match, score = EntityResolver.match_entities("Delhivery Limited", "Delhivery Ltd")
    assert match is True
    assert score >= 0.95

    match_india, score_india = EntityResolver.match_entities("India", "Government of India")
    assert match_india is True

def test_predicate_matching():
    match, score = EntityResolver.match_predicates("revenue", "revenue from operations")
    assert match is True
    assert score == 1.0

    match_gdp, score_gdp = EntityResolver.match_predicates("real GDP growth", "real GDP growth rate")
    assert match_gdp is True
