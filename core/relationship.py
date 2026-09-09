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

        # 6. Value match
        val_match = "UNKNOWN"
        val_diff_pct = None

        if fact_a.value_type in ("numeric", "currency", "percentage") and fact_b.value_type in ("numeric", "currency", "percentage"):
            v1 = fact_a.canonical_value if fact_a.canonical_value is not None else fact_a.numeric_value
            v2 = fact_b.canonical_value if fact_b.canonical_value is not None else fact_b.numeric_value

            if v1 is not None and v2 is not None:
                max_v = max(abs(v1), abs(v2))
                if max_v == 0:
                    val_diff_pct = 0.0
                    val_match = "AGREES"
                else:
                    diff = abs(v1 - v2)
                    val_diff_pct = round((diff / max_v) * 100, 4)

                    if val_diff_pct == 0.0:
                        val_match = "AGREES"
                    elif (fact_a.canonical_unit or "").lower() in ("pin codes", "count") or (fact_b.canonical_unit or "").lower() in ("pin codes", "count"):
                        # Discrete counts cannot use continuous percentage tolerances
                        val_match = "DISAGREES"
                    elif val_diff_pct <= self.value_tolerance_percent:
                        val_match = "TOLERANCE_MATCH"
                    else:
                        val_match = "DISAGREES"
        else:
            # Semantic text comparison
            s1 = str(fact_a.object_value).strip().lower()
            s2 = str(fact_b.object_value).strip().lower()
            tokens1 = set(s1.replace(",", " ").replace(".", " ").split())
            tokens2 = set(s2.replace(",", " ").replace(".", " ").split())
            jaccard = len(tokens1.intersection(tokens2)) / len(tokens1.union(tokens2)) if tokens1 or tokens2 else 0.0

            if s1 == s2 or jaccard >= 0.55:
                val_match = "SEMANTIC_EQUAL"
                val_diff_pct = 0.0
            else:
                val_match = "DISAGREES"
                val_diff_pct = 100.0

        # 7. Source independence
        source_indep = (fact_a.document_id != fact_b.document_id)

        return ComparisonFeatures(
            entity_match=ent_match,
            entity_similarity=ent_sim,
            predicate_match=pred_match,
            predicate_similarity=pred_sim,
            period_match=period_match,
            scope_match=scope_match,
            unit_match=unit_match,
            value_match=val_match,
            value_diff_percent=val_diff_pct,
            source_independence=source_indep
        )

    def classify_relationship(self, features: ComparisonFeatures, fact_a: Fact, fact_b: Fact) -> Tuple[RelationshipType, float, Dict[str, float]]:
        """
        Classify relationship using transparent decision tree.
        Returns: (RelationshipType, overall_confidence, confidence_breakdown)
        """
        breakdown = {
            "entity_score": features.entity_similarity,
            "predicate_score": features.predicate_similarity,
            "period_score": 1.0 if features.period_match == "EXACT" else (0.7 if features.period_match == "OVERLAPPING" else 0.0),
            "scope_score": 1.0 if features.scope_match == "EXACT" else (0.4 if features.scope_match == "DIFFERENT" else 0.7),
            "unit_score": 1.0 if features.unit_match else 0.2,
            "value_score": 1.0 if features.value_match in ("AGREES", "TOLERANCE_MATCH", "SEMANTIC_EQUAL") else 0.0
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

        # If period is OVERLAPPING but not exact, and values differ, it is a contextual difference
        if features.period_match == "OVERLAPPING" and features.value_match == "DISAGREES":
            conf = min(features.entity_similarity, features.predicate_similarity, 0.90)
            return RelationshipType.CONTEXTUAL_DIFFERENCE, conf, breakdown

        # Rule 2: Contextual Difference (Scope Mismatch - Standalone vs Consolidated)
        if features.scope_match == "DIFFERENT":
            conf = min(features.entity_similarity, features.predicate_similarity, 0.95)
            return RelationshipType.CONTEXTUAL_DIFFERENCE, conf, breakdown

        # Rule 3: Contextual Difference (Methodology / Qualifier difference)
        if (fact_a.qualifiers or fact_b.qualifiers) and set(fact_a.qualifiers) != set(fact_b.qualifiers):
            q1 = set(q.lower() for q in fact_a.qualifiers)
            q2 = set(q.lower() for q in fact_b.qualifiers)
            if ("first advance estimates" in q1 and "first advance estimates" not in q2) or \
               ("projection" in q1 and "projection" not in q2):
                conf = 0.90
                return RelationshipType.CONTEXTUAL_DIFFERENCE, conf, breakdown

        # Rule 4: Unit Mismatch
        if not features.unit_match:
            return RelationshipType.UNCERTAIN, 0.60, breakdown

        # Rule 5: Period Unknown on critical financial/macro metrics
        if features.period_match == "UNKNOWN" and (fact_a.value_type in ("numeric", "currency", "percentage") or fact_b.value_type in ("numeric", "currency", "percentage")):
            return RelationshipType.UNCERTAIN, 0.55, breakdown

        # Rule 6: Corroboration (Same entity, predicate, period, scope, units, and values agree)
        if features.value_match in ("AGREES", "TOLERANCE_MATCH", "SEMANTIC_EQUAL"):
            conf = round(min(features.entity_similarity, features.predicate_similarity, fact_a.confidence, fact_b.confidence), 2)
            return RelationshipType.CORROBORATED, conf, breakdown

        # Rule 7: Genuine Contradiction (Exact same context, incompatible values)
        if features.value_match == "DISAGREES" and features.period_match == "EXACT":
            conf = round(min(features.entity_similarity, features.predicate_similarity, fact_a.confidence, fact_b.confidence), 2)
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
