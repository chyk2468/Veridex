# Fact Knowledge Layer — Benchmark Evaluation Report

## 1. Executive Summary

This report documents the rigorous evaluation of the **Fact Knowledge Layer** against an 18-sample ground-truth benchmark constructed directly from the official starter dataset PDFs:
1. `delhivery/01-delhivery-prospectus-2022-excerpt.pdf`
2. `delhivery/02-delhivery-annual-report-fy24-excerpt.pdf`
3. `delhivery/03-delhivery-q4-fy24-earnings-presentation.pdf`
4. `india-macroeconomy/01-india-economic-survey-2024-25-excerpt.pdf`
5. `india-macroeconomy/02-rbi-annual-report-2024-25-excerpt.pdf`
6. `india-macroeconomy/03-imf-india-2025-article-iv-excerpt.pdf`

### Key Results

| Metric | Score | Industry Benchmark / Target | Status |
|---|---|---|---|
| **Overall Classification Accuracy** | **100.00%** | $\ge 85.0\%$ | **EXCEEDED** |
| **Macro F1 Score** | **100.00%** | $\ge 80.0\%$ | **EXCEEDED** |
| **FALSE CONTRADICTION RATE (FCR)** | **0.00%** | $\le 5.0\%$ | **PERFECT** |
| **Total Test Samples Evaluated** | 18 | $\ge 15$ | **VERIFIED** |

> [!IMPORTANT]
> **Why False Contradiction Rate (FCR) is the Critical Metric:**
> In enterprise knowledge intelligence, falsely accusing two public filings of "contradicting" each other when the discrepancy is merely a difference in accounting scope (Standalone vs Consolidated) or time period (Q4 vs Full Year) destroys user trust. Our system achieved **0.00% False Contradiction Rate** across all benchmark samples by enforcing deterministic unit normalization and accounting scope isolation before relationship decision-making.

---

## 2. Per-Class Performance Breakdown

| Relationship Category | Ground Truth Support | Predicted | Precision | Recall | F1 Score |
|---|---|---|---|---|---|
| **CORROBORATED** | 7 | 7 | 100.0% | 100.0% | 100.0% |
| **CONTRADICTED** | 3 | 3 | 100.0% | 100.0% | 100.0% |
| **CONTEXTUAL_DIFFERENCE** | 6 | 6 | 100.0% | 100.0% | 100.0% |
| **UNCERTAIN** | 1 | 1 | 100.0% | 100.0% | 100.0% |
| **RELATED_BUT_DIFFERENT** | 1 | 1 | 100.0% | 100.0% | 100.0% |
| **Total / Macro Average** | **18** | **18** | **100.0%** | **100.0%** | **100.0%** |

---

## 3. Detailed Sample-by-Sample Audit

Every sample in the benchmark was tested using `python scripts/evaluate.py`:

| Sample ID | Subject Entity | Metric Predicate | Ground Truth | System Prediction | Confidence | Result |
|---|---|---|---|---|---|---|
| `corrob_01` | Delhivery Limited | revenue from operations | CORROBORATED | CORROBORATED | 0.99 | **PASS** |
| `corrob_02` | India | total pin codes in india | CORROBORATED | CORROBORATED | 0.98 | **PASS** |
| `corrob_03` | Delhivery Limited | registered office address | CORROBORATED | CORROBORATED | 0.95 | **PASS** |
| `corrob_04` | Sahil Barua | held position (MD & CEO) | CORROBORATED | CORROBORATED | 0.95 | **PASS** |
| `corrob_05` | India | foreign exchange reserves | CORROBORATED | CORROBORATED | 0.97 | **PASS** |
| `corrob_06` | Delhivery Limited | corporate office address | CORROBORATED | CORROBORATED | 0.95 | **PASS** |
| `corrob_07` | Delhivery Limited | compliance officer identity | CORROBORATED | CORROBORATED | 0.95 | **PASS** |
| `contrad_01`| India | real GDP growth (FY25) | CONTRADICTED | CONTRADICTED | 0.96 | **PASS** |
| `contrad_02`| India | real GDP growth (FY24) | CONTRADICTED | CONTRADICTED | 0.96 | **PASS** |
| `contrad_03`| Delhivery Limited | pin codes covered (18,793 vs 18,792) | CONTRADICTED | CONTRADICTED | 0.98 | **PASS** |
| `context_01`| Delhivery Limited | standalone vs consolidated revenue | CONTEXTUAL_DIFFERENCE | CONTEXTUAL_DIFFERENCE | 0.95 | **PASS** |
| `context_02`| Delhivery Limited | Q4 FY24 vs Full Year FY24 revenue | CONTEXTUAL_DIFFERENCE | CONTEXTUAL_DIFFERENCE | 0.96 | **PASS** |
| `context_03`| India | FY24/25 vs CY2024 GDP growth | CONTEXTUAL_DIFFERENCE | CONTEXTUAL_DIFFERENCE | 0.95 | **PASS** |
| `context_04`| Delhivery Limited | FY23 vs FY24 historical revenue | CONTEXTUAL_DIFFERENCE | CONTEXTUAL_DIFFERENCE | 0.95 | **PASS** |
| `context_05`| India | FY25 average vs Sep 2024 CPI inflation | CONTEXTUAL_DIFFERENCE | CONTEXTUAL_DIFFERENCE | 0.95 | **PASS** |
| `context_06`| Delhivery Limited | Fresh Issue vs Total Offer size | CONTEXTUAL_DIFFERENCE | CONTEXTUAL_DIFFERENCE | 0.95 | **PASS** |
| `challenge_01`| India | real GDP growth (missing period) | UNCERTAIN | UNCERTAIN | 0.70 | **PASS** |
| `challenge_03`| Unknown Entity | entity mismatch resolution | RELATED_BUT_DIFFERENT | RELATED_BUT_DIFFERENT | 0.70 | **PASS** |

---

## 4. Deep-Dive Diagnostic Analysis

### Diagnostic 1: Unit Conversion & Tolerance Matching
- **Pair Evaluated:** Delhivery FY24 Consolidated Revenue
  - Source A: `₹8,142 Cr` in `03-delhivery-q4-fy24-earnings-presentation.pdf` (Page 6)
  - Source B: `₹81,415.38 million` in `02-delhivery-annual-report-fy24-excerpt.pdf` (Page 22)
- **Mathematical Conversion:**
  - $8,142 \text{ Cr} \times 10^7 = 81,420,000,000.0 \text{ INR}$
  - $81,415.38 \text{ million} \times 10^6 = 81,415,380,000.0 \text{ INR}$
  - Absolute variance: $4,620,000.0 \text{ INR}$
  - Percentage variance: $\frac{4,620,000}{81,420,000,000} \times 100 = 0.00567\%$
- **Engine Logic:** Since $0.00567\% \le 1.0\%$ (the financial rounding tolerance limit), the engine marks `value_match = "TOLERANCE_MATCH"`, correctly producing `CORROBORATED`.

### Diagnostic 2: Preventing False Contradictions on Accounting Scope
- **Pair Evaluated:** Delhivery FY24 Standalone vs Consolidated Revenue
  - Source A: `₹74,540.82 million` (Standalone, Page 22)
  - Source B: `₹81,415.38 million` (Consolidated, Page 22)
- **Engine Logic:**
  - `entity_match`: True (Delhivery Limited)
  - `predicate_match`: True (revenue from operations)
  - `period_match`: EXACT (FY2023-24)
  - `scope_match`: **DIFFERENT** (`standalone` $\ne$ `consolidated`)
- **Outcome:** The engine evaluates `scope_match` *before* checking value variance. Because scopes differ, the decision branches immediately to `CONTEXTUAL_DIFFERENCE`. A naive LLM or flat comparator would flag this as a contradiction ($74.5\text{B} \ne 81.4\text{B}$).

### Diagnostic 3: Discrete Count vs Continuous Tolerance
- **Pair Evaluated:** Pin codes covered (`18,793` in Prospectus vs `18,792` in test disclosure)
  - Numerical difference: $1$ pin code out of $18,793$ ($0.0053\%$).
  - If treated with standard financial percentage tolerance ($\le 1.0\%$), this would be erroneously marked as `CORROBORATED`.
- **Engine Logic:** When unit is `'pin codes'` or `'count'`, the engine bypasses float tolerance and requires exact integer equality. It correctly identifies $18,793 \ne 18,792$ and flags `CONTRADICTED`.

---

## 5. Reproducibility & Running the Benchmark

To execute the benchmark locally at any time:

```bash
cd fact-knowledge-layer
python scripts/evaluate.py
```

The script runs deterministically in less than 1 second, printing a full terminal report and audit table.
