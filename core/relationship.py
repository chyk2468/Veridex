"""
Deterministic Relationship Engine.
Evaluates fact pairs through deterministic feature comparison and rule-based decision logic.
Strictly adheres to Rule 2: LLM NEVER decides relationships; Python evaluates deterministic features.
"""

import uuid
import logging
from typing import Tuple, Dict, Any, Optional
from models.fact import Fact
from models.relationship import Relationship, RelationshipType, ComparisonFeatures
from core.entity_resolver import EntityResolver
from core.config import settings

logger = logging.getLogger(__name__)

class RelationshipEngine:
    """Classifies relationships between facts using transparent, explainable feature comparison."""

    def __init__(self, value_tolerance_percent: float = 1.0):
        self.value_tolerance_percent = value_tolerance_percent

    def extract_features(self, fact_a: Fact, fact_b: Fact) -> ComparisonFeatures:
        """Deterministically compute all comparative features between two facts."""
        # 1. Entity match
        ent_match, ent_sim = EntityResolver.match_entities(fact_a.subject, fact_b.subject)

        # 2. Predicate match
        pred_match, pred_sim = EntityResolver.match_predicates(fact_a.predicate, fact_b.predicate)

        # 3. Period match
        period_match = "UNKNOWN"
        if fact_a.period and fact_b.period:
            if fact_a.period.is_exact_match(fact_b.period):
                period_match = "EXACT"
            elif fact_a.period.overlaps(fact_b.period):
                period_match = "OVERLAPPING"
            else:
                period_match = "DIFFERENT"
        elif not fact_a.period and not fact_b.period:
            period_match = "EXACT"  # both timeless / general facts

        # 4. Scope match (standalone vs consolidated, geographic)
        scope_match = "EXACT"
        if fact_a.business_scope and fact_b.business_scope:
            if fact_a.business_scope.lower() != fact_b.business_scope.lower():
                scope_match = "DIFFERENT"
        elif (fact_a.business_scope and not fact_b.business_scope) or (not fact_a.business_scope and fact_b.business_scope):
            # One specified standalone/consolidated while other didn't
            if any(s in ("standalone", "consolidated") for s in [fact_a.business_scope, fact_b.business_scope]):
                scope_match = "DIFFERENT"

        if fact_a.geographic_scope and fact_b.geographic_scope:
            if fact_a.geographic_scope.lower() != fact_b.geographic_scope.lower():
                scope_match = "DIFFERENT"

        # 5. Unit match
        unit_match = True
        if fact_a.canonical_unit and fact_b.canonical_unit:
            u_a = fact_a.canonical_unit.lower()
            u_b = fact_b.canonical_unit.lower()
            unit_match = (u_a == u_b) or (u_a in ("inr", "cr", "million") and u_b in ("inr", "cr", "million"))
        elif (fact_a.canonical_unit or fact_b.canonical_unit) and fact_a.value_type == "numeric":
            unit_match = False

        # 6. Value match & Metric variance analysis
        val_match = "NOT_COMPARABLE"
        variance_type = "NOT_COMPARABLE"
        val_diff_pct = None
        val_diff_abs = None

        if fact_a.value_type in ("numeric", "currency", "percentage") and fact_b.value_type in ("numeric", "currency", "percentage"):
            v1 = fact_a.canonical_value if fact_a.canonical_value is not None else fact_a.numeric_value
            v2 = fact_b.canonical_value if fact_b.canonical_value is not None else fact_b.numeric_value

            if v1 is not None and v2 is not None:
                diff = abs(v1 - v2)
                val_diff_abs = round(diff, 4)
                max_v = max(abs(v1), abs(v2))

                if max_v == 0:
                    val_diff_pct = 0.0
                    val_match = "EXACT_MATCH"
                    variance_type = "EXACT_MATCH"
                else:
                    val_diff_pct = round((diff / max_v) * 100, 4)

                    if val_diff_pct == 0.0:
                        val_match = "EXACT_MATCH"
                        variance_type = "EXACT_MATCH"
                    elif (fact_a.canonical_unit or "").lower() in ("pin codes", "count", "facilities", "units") or \
                         (fact_b.canonical_unit or "").lower() in ("pin codes", "count", "facilities", "units"):
                        # Discrete integer counts cannot use continuous percentage tolerances
                        val_match = "MATERIAL_DIFFERENCE"
                        variance_type = "MATERIAL_DIFFERENCE"
                    elif val_diff_pct <= self.value_tolerance_percent:
                        val_match = "ROUNDING_VARIANCE"
                        variance_type = "ROUNDING_VARIANCE"
                    else:
                        val_match = "MATERIAL_DIFFERENCE"
                        variance_type = "MATERIAL_DIFFERENCE"
        else:
            # Semantic text comparison
            s1 = str(fact_a.object_value).strip().lower()
            s2 = str(fact_b.object_value).strip().lower()
            tokens1 = set(s1.replace(",", " ").replace(".", " ").split())
            tokens2 = set(s2.replace(",", " ").replace(".", " ").split())
            jaccard = len(tokens1.intersection(tokens2)) / len(tokens1.union(tokens2)) if tokens1 or tokens2 else 0.0

            if s1 == s2 or jaccard >= 0.55:
                val_match = "SEMANTIC_EQUAL"
                variance_type = "EXACT_MATCH"
                val_diff_pct = 0.0
                val_diff_abs = 0.0
            else:
                val_match = "MATERIAL_DIFFERENCE"
                variance_type = "MATERIAL_DIFFERENCE"
                val_diff_pct = 100.0

        # 7. Estimate / Vintage check
        est_match = "EXACT"
        q1_all = [q.lower() for q in (fact_a.qualifiers or [])] + ([fact_a.estimate_status.lower()] if fact_a.estimate_status else [])
        q2_all = [q.lower() for q in (fact_b.qualifiers or [])] + ([fact_b.estimate_status.lower()] if fact_b.estimate_status else [])
        
        is_est_a = any(k in q1_all for k in ["estimate", "advance_estimate", "first advance estimates", "projection"])
        is_est_b = any(k in q2_all for k in ["estimate", "advance_estimate", "first advance estimates", "projection"])
        if is_est_a != is_est_b or (is_est_a and is_est_b and set(q1_all) != set(q2_all)):
            est_match = "DIVERGENT"

        # 8. Source independence & upstream source check
        source_indep = (fact_a.document_id != fact_b.document_id)
        upstream_match = None
        if fact_a.upstream_source and fact_b.upstream_source:
            upstream_match = (fact_a.upstream_source.strip().lower() == fact_b.upstream_source.strip().lower())

        return ComparisonFeatures(
            entity_match=ent_match,
            entity_similarity=ent_sim,
            predicate_match=pred_match,
            predicate_similarity=pred_sim,
            period_match=period_match,
            scope_match=scope_match,
            unit_match=unit_match,
            value_match=val_match,
            numeric_variance_type=variance_type,
            value_diff_percent=val_diff_pct,
            value_diff_absolute=val_diff_abs,
            estimate_match=est_match,
            source_independence=source_indep,
            upstream_source_match=upstream_match
        )

    def classify_relationship(self, features: ComparisonFeatures, fact_a: Fact, fact_b: Fact) -> Tuple[RelationshipType, float, Dict[str, float]]:
        """
        Classify relationship using transparent, audit-ready decision rules.
        Returns: (RelationshipType, overall_confidence, confidence_breakdown)
        """
        is_val_agree = features.value_match in ("EXACT_MATCH", "ROUNDING_VARIANCE", "SEMANTIC_EQUAL", "AGREES", "TOLERANCE_MATCH")

        breakdown = {
            "entity_score": features.entity_similarity,
            "predicate_score": features.predicate_similarity,
            "period_score": 1.0 if features.period_match == "EXACT" else (0.7 if features.period_match == "OVERLAPPING" else 0.0),
            "scope_score": 1.0 if features.scope_match == "EXACT" else (0.4 if features.scope_match == "DIFFERENT" else 0.7),
            "unit_score": 1.0 if features.unit_match else 0.2,
            "value_score": 1.0 if is_val_agree else 0.0
        }

        # Guard: Entity mismatch
        if not features.entity_match:
            return RelationshipType.RELATED_BUT_DIFFERENT, 0.50, breakdown

        # Guard: Predicate mismatch
        if not features.predicate_match:
            return RelationshipType.RELATED_BUT_DIFFERENT, 0.75, breakdown

        # Rule 1: Contextual Difference (Period Mismatch or Overlapping but different period bounds)
        if features.period_match == "DIFFERENT":
            conf = min(features.entity_similarity, features.predicate_similarity, 0.95)
            return RelationshipType.CONTEXTUAL_DIFFERENCE, conf, breakdown

        # If period is OVERLAPPING but not exact, and values differ materially, it is a contextual difference
        if features.period_match == "OVERLAPPING" and not is_val_agree:
            conf = min(features.entity_similarity, features.predicate_similarity, 0.90)
            return RelationshipType.CONTEXTUAL_DIFFERENCE, conf, breakdown

        # Rule 2: Contextual Difference (Scope Mismatch - Standalone vs Consolidated)
        if features.scope_match == "DIFFERENT":
            conf = min(features.entity_similarity, features.predicate_similarity, 0.95)
            return RelationshipType.CONTEXTUAL_DIFFERENCE, conf, breakdown

        # Rule 3: Contextual Difference (Methodology / Accounting Base Qualifier difference)
        if (fact_a.qualifiers or fact_b.qualifiers) and set(fact_a.qualifiers) != set(fact_b.qualifiers):
            q1 = set(q.lower() for q in fact_a.qualifiers)
            q2 = set(q.lower() for q in fact_b.qualifiers)
            if ("restated" in q1 and "restated" not in q2) or ("pro-forma" in q1 and "pro-forma" not in q2):
                conf = 0.90
                return RelationshipType.CONTEXTUAL_DIFFERENCE, conf, breakdown

        # Rule 4: Unit Mismatch
        if not features.unit_match:
            return RelationshipType.UNCERTAIN, 0.60, breakdown

        # Rule 5: Period Unknown on critical financial/macro metrics
        if features.period_match == "UNKNOWN" and (fact_a.value_type in ("numeric", "currency", "percentage") or fact_b.value_type in ("numeric", "currency", "percentage")):
            return RelationshipType.UNCERTAIN, 0.55, breakdown

        # Rule 6: Corroboration (Same entity, predicate, period, scope, units, and values agree)
        if is_val_agree:
            conf = round(min(features.entity_similarity, features.predicate_similarity, fact_a.confidence, fact_b.confidence), 2)
            return RelationshipType.CORROBORATED, conf, breakdown

        # Rule 7: Genuine or Likely Contradiction (Exact same context, material value disagreement)
        if features.period_match == "EXACT":
            conf = round(min(features.entity_similarity, features.predicate_similarity, fact_a.confidence, fact_b.confidence), 2)
            
            # Check if divergence is due to estimation/projection status
            if features.estimate_match == "DIVERGENT":
                return RelationshipType.LIKELY_CONTRADICTION, conf, breakdown
            
            return RelationshipType.CONTRADICTED, conf, breakdown

        return RelationshipType.UNCERTAIN, 0.50, breakdown

    def evaluate_pair(self, fact_a: Fact, fact_b: Fact) -> Relationship:
        """Evaluate a pair of facts and return a fully populated Relationship model."""
        features = self.extract_features(fact_a, fact_b)
        rel_type, conf, breakdown = self.classify_relationship(features, fact_a, fact_b)

        rel_id = f"rel_{uuid.uuid4().hex[:10]}"

        return Relationship(
            relationship_id=rel_id,
            fact_a_id=fact_a.fact_id,
            fact_b_id=fact_b.fact_id,
            relationship_type=rel_type,
            comparison_features=features.model_dump(),
            confidence=conf,
            confidence_breakdown=breakdown,
            explanation="",  # Generated by explanation engine
            evidence_a_id=fact_a.evidence_id,
            evidence_b_id=fact_b.evidence_id
        )

    def compare_facts(self, fact_a: Fact, fact_b: Fact) -> Tuple[str, ComparisonFeatures, float]:
        """Convenience method returning (rel_type_str, features, confidence)."""
        features = self.extract_features(fact_a, fact_b)
        rel_type, conf, breakdown = self.classify_relationship(features, fact_a, fact_b)
        val = rel_type.value if hasattr(rel_type, "value") else str(rel_type)
        return val, features, conf

