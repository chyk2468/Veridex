"""
Ground Truth Evaluation Benchmark Dataset.
Constructed directly from verified disclosures in the starter dataset PDFs:
- Delhivery Prospectus, Annual Report FY24, and Q4 FY24 Presentation
- India Economic Survey 2024-25, RBI Annual Report 2024-25, IMF 2025 Article IV
"""

from typing import List, Dict, Any

# Benchmark ground truth pairs across the 4 primary relationship categories
EVALUATION_BENCHMARK = [
    # =========================================================================
    # 1. CORROBORATIONS (Values agree across independent sources/disclosures)
    # =========================================================================
    {
        "id": "corrob_01",
        "category": "CORROBORATED",
        "fact_a": {
            "subject": "Delhivery Limited", "predicate": "revenue from operations",
            "value": 8142, "unit": "Cr", "canonical_value": 81420000000.0, "canonical_unit": "INR",
            "period": "FY2023-24", "business_scope": "consolidated",
            "doc": "03-delhivery-q4-fy24-earnings-presentation.pdf", "page": 6
        },
        "fact_b": {
            "subject": "Delhivery Limited", "predicate": "revenue from operations",
            "value": 81415.38, "unit": "million", "canonical_value": 81415380000.0, "canonical_unit": "INR",
            "period": "FY 2023-24", "business_scope": "consolidated",
            "doc": "02-delhivery-annual-report-fy24-excerpt.pdf", "page": 22
        },
        "expected_relationship": "CORROBORATED",
        "notes": "Consolidated FY24 revenue agrees within 0.0057% rounding tolerance between presentation and statutory annual report."
    },
    {
        "id": "corrob_02",
        "category": "CORROBORATED",
        "fact_a": {
            "subject": "India", "predicate": "total pin codes in india",
            "value": 19300, "unit": "pin codes", "canonical_value": 19300, "canonical_unit": "pin codes",
            "period": None, "business_scope": None,
            "doc": "03-delhivery-q4-fy24-earnings-presentation.pdf", "page": 8
        },
        "fact_b": {
            "subject": "India", "predicate": "total pin codes in india",
            "value": 19300, "unit": "pin codes", "canonical_value": 19300, "canonical_unit": "pin codes",
            "period": None, "business_scope": None,
            "doc": "02-delhivery-annual-report-fy24-excerpt.pdf", "page": 7
        },
        "expected_relationship": "CORROBORATED",
        "notes": "Exact match for India Post pin code universe."
    },
    {
        "id": "corrob_03",
        "category": "CORROBORATED",
        "fact_a": {
            "subject": "Delhivery Limited", "predicate": "registered office address",
            "value": "Air Cargo Logistics Centre-II, Opposite Gate 6 Cargo Terminal, IGI Airport, New Delhi 110037",
            "value_type": "semantic", "unit": None, "canonical_value": None, "canonical_unit": None,
            "period": None, "business_scope": None,
            "doc": "01-delhivery-prospectus-2022-excerpt.pdf", "page": 1
        },
        "fact_b": {
            "subject": "Delhivery Limited", "predicate": "registered office address",
            "value": "Air Cargo Logistics Centre-II, Opposite Gate 6 Cargo Terminal, IGI Airport, New Delhi 110037",
            "value_type": "semantic", "unit": None, "canonical_value": None, "canonical_unit": None,
            "period": None, "business_scope": None,
            "doc": "02-delhivery-annual-report-fy24-excerpt.pdf", "page": 31
        },
        "expected_relationship": "CORROBORATED",
        "notes": "Exact match for corporate statutory registered office."
    },
    {
        "id": "corrob_04",
        "category": "CORROBORATED",
        "fact_a": {
            "subject": "Sahil Barua", "predicate": "held position",
            "value": "Managing Director & CEO at Delhivery Limited",
            "value_type": "semantic", "unit": None, "canonical_value": None, "canonical_unit": None,
            "period": "FY2023-24", "business_scope": None,
            "doc": "02-delhivery-annual-report-fy24-excerpt.pdf", "page": 40
        },
        "fact_b": {
            "subject": "Sahil Barua", "predicate": "held position",
            "value": "Managing Director & CEO at Delhivery Limited",
            "value_type": "semantic", "unit": None, "canonical_value": None, "canonical_unit": None,
            "period": "FY2023-24", "business_scope": None,
            "doc": "02-delhivery-annual-report-fy24-excerpt.pdf", "page": 49
        },
        "expected_relationship": "CORROBORATED",
        "notes": "Semantic agreement on executive designation."
    },
    {
        "id": "corrob_05",
        "category": "CORROBORATED",
        "fact_a": {
            "subject": "India", "predicate": "foreign exchange reserves",
            "value": 650, "unit": "billion USD", "canonical_value": 650000000000.0, "canonical_unit": "USD",
            "period": "2024-25", "business_scope": None,
            "doc": "02-rbi-annual-report-2024-25-excerpt.pdf", "page": 22
        },
        "fact_b": {
            "subject": "India", "predicate": "foreign exchange reserves",
            "value": 650, "unit": "billion USD", "canonical_value": 650000000000.0, "canonical_unit": "USD",
            "period": "2024-25", "business_scope": None,
            "doc": "03-imf-india-2025-article-iv-excerpt.pdf", "page": 11
        },
        "expected_relationship": "CORROBORATED",
        "notes": "Both reports state foreign exchange reserves of ~US$650 billion."
    },

    # =========================================================================
    # 2. CONTRADICTIONS & ESTIMATE DIVERGENCES
    # =========================================================================
    {
        "id": "contrad_01",
        "category": "LIKELY_CONTRADICTION",
        "fact_a": {
            "subject": "India", "predicate": "real GDP growth",
            "value": 6.4, "unit": "%", "canonical_value": 6.4, "canonical_unit": "percent",
            "period": "FY2024/25", "business_scope": None,
            "estimate_status": "advance_estimate",
            "publication_date": "July 2024",
            "upstream_source": "Ministry of Finance (Economic Survey)",
            "doc": "01-india-economic-survey-2024-25-excerpt.pdf", "page": 4
        },
        "fact_b": {
            "subject": "India", "predicate": "real GDP growth",
            "value": 6.5, "unit": "%", "canonical_value": 6.5, "canonical_unit": "percent",
            "period": "FY2024/25", "business_scope": None,
            "estimate_status": "projection",
            "publication_date": "January 2025",
            "upstream_source": "IMF Staff Consultations",
            "doc": "03-imf-india-2025-article-iv-excerpt.pdf", "page": 10
        },
        "expected_relationship": "LIKELY_CONTRADICTION",
        "notes": "Economic Survey reports 6.4% as July 2024 advance estimate while IMF projects 6.5% in January 2025. Divergence is classified as LIKELY_CONTRADICTION due to estimation vintage."
    },
    {
        "id": "contrad_02",
        "category": "LIKELY_CONTRADICTION",
        "fact_a": {
            "subject": "India", "predicate": "real GDP growth",
            "value": 6.5, "unit": "%", "canonical_value": 6.5, "canonical_unit": "percent",
            "period": "FY2025/26", "business_scope": None,
            "estimate_status": "projection",
            "publication_date": "May 2024",
            "qualifiers": ["RBI baseline projection"],
            "upstream_source": "RBI Monetary Policy Department",
            "doc": "02-rbi-annual-report-2024-25-excerpt.pdf", "page": 17
        },
        "fact_b": {
            "subject": "India", "predicate": "real GDP growth",
            "value": 6.6, "unit": "%", "canonical_value": 6.6, "canonical_unit": "percent",
            "period": "FY2025/26", "business_scope": None,
            "estimate_status": "projection",
            "publication_date": "January 2025",
            "qualifiers": ["IMF Article IV staff baseline"],
            "upstream_source": "IMF Mission Staff",
            "doc": "03-imf-india-2025-article-iv-excerpt.pdf", "page": 13
        },
        "expected_relationship": "LIKELY_CONTRADICTION",
        "notes": "RBI projects 6.5% for FY2025/26 (May 2024 baseline) while IMF projects 6.6% (January 2025 baseline). Vintage and model differences make this a LIKELY_CONTRADICTION."
    },
    {
        "id": "contrad_03",
        "category": "CONTRADICTED",
        "fact_a": {
            "subject": "Delhivery Limited", "predicate": "pin codes covered",
            "value": 18793, "unit": "pin codes", "canonical_value": 18793, "canonical_unit": "pin codes",
            "period": "FY2023-24", "business_scope": None,
            "estimate_status": "actual",
            "doc": "02-delhivery-annual-report-fy24-excerpt.pdf", "page": 22
        },
        "fact_b": {
            "subject": "Delhivery Limited", "predicate": "pin codes covered",
            "value": 18792, "unit": "pin codes", "canonical_value": 18792, "canonical_unit": "pin codes",
            "period": "FY2023-24", "business_scope": None,
            "estimate_status": "actual",
            "doc": "03-delhivery-q4-fy24-earnings-presentation.pdf", "page": 8
        },
        "expected_relationship": "CONTRADICTED",
        "notes": "Statutory report states 18,793 pin codes while presentation states 18,792 for the same FY24 period. Discrete count disagreement constitutes an un-reconciled CONTRADICTION."
    },

    # =========================================================================
    # 3. CONTEXTUAL DIFFERENCES (Apparent conflict resolved by context)
    # =========================================================================
    {
        "id": "context_01",
        "category": "CONTEXTUAL_DIFFERENCE",
        "fact_a": {
            "subject": "Delhivery Limited", "predicate": "revenue from operations",
            "value": 74540.82, "unit": "million", "canonical_value": 74540820000.0, "canonical_unit": "INR",
            "period": "FY 2023-24", "business_scope": "standalone",
            "doc": "02-delhivery-annual-report-fy24-excerpt.pdf", "page": 22
        },
        "fact_b": {
            "subject": "Delhivery Limited", "predicate": "revenue from operations",
            "value": 81415.38, "unit": "million", "canonical_value": 81415380000.0, "canonical_unit": "INR",
            "period": "FY 2023-24", "business_scope": "consolidated",
            "doc": "02-delhivery-annual-report-fy24-excerpt.pdf", "page": 22
        },
        "expected_relationship": "CONTEXTUAL_DIFFERENCE",
        "notes": "Difference explained by accounting scope: Standalone (₹74,540.82M) vs Consolidated (₹81,415.38M)."
    },
    {
        "id": "context_02",
        "category": "CONTEXTUAL_DIFFERENCE",
        "fact_a": {
            "subject": "Delhivery Limited", "predicate": "revenue from operations",
            "value": 2076, "unit": "Cr", "canonical_value": 20760000000.0, "canonical_unit": "INR",
            "period": "Q4 FY2023-24", "business_scope": "consolidated",
            "doc": "03-delhivery-q4-fy24-earnings-presentation.pdf", "page": 7
        },
        "fact_b": {
            "subject": "Delhivery Limited", "predicate": "revenue from operations",
            "value": 8142, "unit": "Cr", "canonical_value": 81420000000.0, "canonical_unit": "INR",
            "period": "FY2023-24", "business_scope": "consolidated",
            "doc": "03-delhivery-q4-fy24-earnings-presentation.pdf", "page": 6
        },
        "expected_relationship": "CONTEXTUAL_DIFFERENCE",
        "notes": "Difference explained by reporting period: Q4 FY24 (₹2,076 Cr) vs Full Year FY24 (₹8,142 Cr)."
    },
    {
        "id": "context_03",
        "category": "CONTEXTUAL_DIFFERENCE",
        "fact_a": {
            "subject": "India", "predicate": "real GDP growth",
            "value": 6.5, "unit": "%", "canonical_value": 6.5, "canonical_unit": "percent",
            "period": "Q1 FY2024/25", "business_scope": None,
            "doc": "02-rbi-annual-report-2024-25-excerpt.pdf", "page": 24
        },
        "fact_b": {
            "subject": "India", "predicate": "real GDP growth",
            "value": 6.5, "unit": "%", "canonical_value": 6.5, "canonical_unit": "percent",
            "period": "FY2024/25", "business_scope": None,
            "doc": "03-imf-india-2025-article-iv-excerpt.pdf", "page": 10
        },
        "expected_relationship": "CONTEXTUAL_DIFFERENCE",
        "notes": "Same number (6.5%), but one is Q1 actual and the other is Full Year actual."
    },
    {
        "id": "context_04",
        "category": "CONTEXTUAL_DIFFERENCE",
        "fact_a": {
            "subject": "Delhivery Limited", "predicate": "revenue from operations",
            "value": 81415.38, "unit": "million", "canonical_value": 81415380000.0, "canonical_unit": "INR",
            "period": "FY 2023-24", "business_scope": "consolidated",
            "doc": "02-delhivery-annual-report-fy24-excerpt.pdf", "page": 22
        },
        "fact_b": {
            "subject": "Delhivery Limited", "predicate": "revenue from operations",
            "value": 72253.01, "unit": "million", "canonical_value": 72253010000.0, "canonical_unit": "INR",
            "period": "FY 2022-23", "business_scope": "consolidated",
            "doc": "02-delhivery-annual-report-fy24-excerpt.pdf", "page": 22
        },
        "expected_relationship": "CONTEXTUAL_DIFFERENCE",
        "notes": "YoY reporting comparison: FY24 vs FY23 revenue."
    },

    # =========================================================================
    # 4. EXTRACTION / REASONING CHALLENGES (Ambiguity or Incomplete Context)
    # =========================================================================
    {
        "id": "challenge_01",
        "category": "UNCERTAIN",
        "fact_a": {
            "subject": "India", "predicate": "real GDP growth",
            "value": 6.5, "unit": "%", "canonical_value": 6.5, "canonical_unit": "percent",
            "period": None, "business_scope": None,
            "doc": "raw_snippet", "page": 1
        },
        "fact_b": {
            "subject": "India", "predicate": "real GDP growth",
            "value": 6.4, "unit": "%", "canonical_value": 6.4, "canonical_unit": "percent",
            "period": "FY2024/25", "business_scope": None,
            "doc": "01-india-economic-survey-2024-25-excerpt.pdf", "page": 4
        },
        "expected_relationship": "UNCERTAIN",
        "notes": "Missing period in Fact A prevents certain classification as contradiction."
    },
    # Additional Corroborations
    {
        "id": "corrob_06",
        "category": "CORROBORATED",
        "fact_a": {
            "subject": "Delhivery Limited", "predicate": "corporate office address",
            "value": "Plot 5, Sector 44, Gurugram 122002, Haryana, India",
            "value_type": "semantic", "unit": None, "canonical_value": None, "canonical_unit": None,
            "period": None, "business_scope": None,
            "doc": "01-delhivery-prospectus-2022-excerpt.pdf", "page": 1
        },
        "fact_b": {
            "subject": "Delhivery Limited", "predicate": "corporate office address",
            "value": "Plot No. 5, Sector 44, Gurugram, Haryana 122001",
            "value_type": "semantic", "unit": None, "canonical_value": None, "canonical_unit": None,
            "period": None, "business_scope": None,
            "doc": "02-delhivery-annual-report-fy24-excerpt.pdf", "page": 51
        },
        "expected_relationship": "CORROBORATED",
        "notes": "Corporate office address confirmed across filings."
    },
    {
        "id": "corrob_07",
        "category": "CORROBORATED",
        "fact_a": {
            "subject": "Delhivery Limited", "predicate": "compliance officer",
            "value": "Sunil Kumar Bansal",
            "value_type": "semantic", "unit": None, "canonical_value": None, "canonical_unit": None,
            "period": None, "business_scope": None,
            "doc": "01-delhivery-prospectus-2022-excerpt.pdf", "page": 1
        },
        "fact_b": {
            "subject": "Delhivery Limited", "predicate": "compliance officer",
            "value": "Sunil Kumar Bansal",
            "value_type": "semantic", "unit": None, "canonical_value": None, "canonical_unit": None,
            "period": "FY2023-24", "business_scope": None,
            "doc": "02-delhivery-annual-report-fy24-excerpt.pdf", "page": 50
        },
        "expected_relationship": "CORROBORATED",
        "notes": "Company Secretary and Compliance Officer identity match."
    },

    # Additional Contextual Differences
    {
        "id": "context_05",
        "category": "CONTEXTUAL_DIFFERENCE",
        "fact_a": {
            "subject": "India", "predicate": "headline CPI inflation",
            "value": 4.6, "unit": "%", "canonical_value": 4.6, "canonical_unit": "percent",
            "period": "2024-25", "business_scope": None,
            "doc": "02-rbi-annual-report-2024-25-excerpt.pdf", "page": 17
        },
        "fact_b": {
            "subject": "India", "predicate": "headline CPI inflation",
            "value": 1.5, "unit": "%", "canonical_value": 1.5, "canonical_unit": "percent",
            "period": "CY2024", "business_scope": None,
            "doc": "03-imf-india-2025-article-iv-excerpt.pdf", "page": 10
        },
        "expected_relationship": "CONTEXTUAL_DIFFERENCE",
        "notes": "Full year FY25 average (4.6%) vs single month September 2024 print (1.5%)."
    },
    {
        "id": "context_06",
        "category": "CONTEXTUAL_DIFFERENCE",
        "fact_a": {
            "subject": "Delhivery Limited", "predicate": "revenue from operations",
            "value": 40000, "unit": "million", "canonical_value": 40000000000.0, "canonical_unit": "INR",
            "period": "FY2022", "business_scope": "fresh_issue",
            "doc": "01-delhivery-prospectus-2022-excerpt.pdf", "page": 1
        },
        "fact_b": {
            "subject": "Delhivery Limited", "predicate": "revenue from operations",
            "value": 52350, "unit": "million", "canonical_value": 52350000000.0, "canonical_unit": "INR",
            "period": "FY2022", "business_scope": "total_offer",
            "doc": "01-delhivery-prospectus-2022-excerpt.pdf", "page": 1
        },
        "expected_relationship": "CONTEXTUAL_DIFFERENCE",
        "notes": "Different scope: Fresh issue component (₹40,000M) vs Total Offer (₹52,350M)."
    },

    # Additional Uncertainties
    {
        "id": "challenge_03",
        "category": "UNCERTAIN",
        "fact_a": {
            "subject": "Unknown Entity", "predicate": "revenue from operations",
            "value": 1000, "unit": "Cr", "canonical_value": 10000000000.0, "canonical_unit": "INR",
            "period": "FY2023-24", "business_scope": "consolidated",
            "doc": "snippet", "page": 1
        },
        "fact_b": {
            "subject": "Delhivery Limited", "predicate": "revenue from operations",
            "value": 8142, "unit": "Cr", "canonical_value": 81420000000.0, "canonical_unit": "INR",
            "period": "FY2023-24", "business_scope": "consolidated",
            "doc": "03-delhivery-q4-fy24-earnings-presentation.pdf", "page": 6
        },
        "expected_relationship": "RELATED_BUT_DIFFERENT",
        "notes": "Entity mismatch prevents direct corroboration or contradiction."
    }
]

def get_benchmark_dataset() -> List[Dict[str, Any]]:
    """Return the ground truth evaluation benchmark dataset."""
    return EVALUATION_BENCHMARK

FAILURE_ANALYSIS_CASES = [
    {
        "failure_id": "fail_01",
        "failure_type": "MULTI_COLUMN_TABLE_LAYOUT",
        "title": "Multi-Column Table Cell-to-Header Misattribution",
        "description": "In multi-column financial statements (e.g. Segment Reporting tables with Standalone and Consolidated side-by-side), naive text extraction or single-pass LLMs attribute figures from the 'Standalone' column to the 'Consolidated' header.",
        "root_cause": "Visual proximity vs logical column hierarchy: PyMuPDF bounding boxes extract left-to-right reading order across columns unless table bounding grids are reconstructed.",
        "how_system_flags": "Confidence scoring is penalized when header coordinates do not vertically align with cell x-coordinates. TableParser extracts explicit grid cells and retains column hierarchy.",
        "how_system_mitigates": "TableParser (pdfplumber) detects table bounding rectangles, extracts structural grid columns, and enforces that business_scope is inherited from the parent column header.",
        "status": "MITIGATED"
    },
    {
        "failure_id": "fail_02",
        "failure_type": "QUALIFIER_OMISSION",
        "title": "Accounting Qualifier and Restatement Omission",
        "description": "Financial statements often disclose restated prior-period figures alongside original figures. If qualifiers like 'restated', 'pro-forma', or 'before exceptional items' are omitted, the system could flag false contradictions.",
        "root_cause": "LLM fact extractors tend to focus strictly on (Subject, Predicate, Value) triplets and drop trailing parentheticals or footnote references (e.g. 'Note 34 - Restated for Amalgamation').",
        "how_system_flags": "Fact model includes explicit `qualifiers: List[str]` and `notes: Optional[str]`. If qualifiers differ between two facts, scope_match is marked as DIFFERENT or UNCERTAIN.",
        "how_system_mitigates": "Chunker extracts footnote blocks within 50pt of table boundaries and passes them into the prompt. RelationshipEngine marks facts with conflicting qualifiers as CONTEXTUAL_DIFFERENCE rather than CONTRADICTED.",
        "status": "MITIGATED"
    },
    {
        "failure_id": "fail_03",
        "failure_type": "DISCRETE_COUNT_TOLERANCE_ERROR",
        "title": "Continuous Percentage Tolerance Applied to Discrete Counts",
        "description": "Delhivery network pin code reach is reported as 18,793 pin codes in Prospectus vs 18,792 pin codes in another disclosure. If a generic 1.0% tolerance is used, the system would falsely classify this as CORROBORATED because diff is 0.0053%.",
        "root_cause": "Treating integer counting units (pin codes, facilities, fleet size) with floating-point financial rounding tolerances.",
        "how_system_flags": "Unit-specific evaluation logic in RelationshipEngine: When unit is 'pin codes' or 'count', value_diff_percent is bypassed and exact integer equality is required.",
        "how_system_mitigates": "RelationshipEngine explicitly checks `if canonical_unit in ('pin codes', 'count'): val_match = 'DISAGREES' if diff != 0`. Correctly classifies 18,793 vs 18,792 as CONTRADICTED.",
        "status": "RESOLVED"
    }
]
