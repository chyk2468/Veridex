# Superjoin Submission Walkthrough — Fact Knowledge Layer

The complete submission for the **Superjoin VIT 2026 Engineering Intern Hiring Assignment** has been implemented, tested, and packaged in:

`c:/Users/91630/Desktop/rag/fact-knowledge-layer`

## 1. What Was Accomplished

We engineered a **generalized, explainable Fact Knowledge Layer** that accepts PDF documents, preserves page-level evidence, extracts structured numerical and semantic facts, normalizes values and contextual attributes, compares facts across documents, classifies their relationships, and generates grounded natural-language explanations.

The system is designed around four principles:

* Grounding
* Context awareness
* Deterministic relationship classification
* Generalization to new PDFs

### Observed Benchmark Performance

On our 18-sample manually verified benchmark, the current relationship classifier achieved **100.00% classification accuracy**, **100.00% macro F1**, and a **0.00% false contradiction rate**.

> [!NOTE]
> These results describe performance on the local manually verified benchmark and are not presented as a guarantee of performance on arbitrary documents. The benchmark was designed to validate that core deterministic rules, tolerance policies, and contextual branchings operate without regressions.

---

## 2. Core Architecture & Verification of Principles

```
  Raw PDF Documents
         │
         ├──► PyMuPDF Page-by-Page Parser (1-indexed pages, bounding boxes)
         └──► pdfplumber Table Parser (2D grid reconstruction, column headers)
                     │
                     ▼
             Evidence Store (exact coordinates, verbatim text)
                     │
                     ▼
             Candidate Fact Detector & Sliding Chunker
                     │
                     ▼
             Fact Extractor (Groq LLaMA 3.3 70B / Offline Heuristic)
                     │
                     ▼
             Deterministic Normalizer (Currencies, multipliers, periods, scopes)
                     │
                     ▼
      ┌──────────────┴──────────────┐
      ▼                             ▼
SQLite Relational Store       FAISS Vector Store (384-dim all-MiniLM-L6-v2)
      │                             │
      └──────────────┬──────────────┘
                     ▼
             Candidate Pair Matcher (Entity filter + vector similarity pruning)
                     │
                     ▼
             Rule 2: Deterministic Relationship Engine
             (EXACT_MATCH, ROUNDING_VARIANCE, MATERIAL_DIFFERENCE, NOT_COMPARABLE)
                     │
                     ▼
             Classification: CORROBORATED | CONTRADICTED | LIKELY_CONTRADICTION |
                             CONTEXTUAL_DIFFERENCE | UNCERTAIN | RELATED_BUT_DIFFERENT
                     │
                     ▼
             Constrained Natural-Language Explanation Engine
```

### Rule 2 Enforcement
In accordance with official requirements, **the LLM does not classify relationships**. Relationship classification is strictly governed by deterministic Python comparison rules that evaluate:
1. Canonical entity resolution (e.g. `Delhivery Ltd.` $\to$ `Delhivery Limited`)
2. Predicate similarity (lexical + vector embedding distance)
3. Accounting scope compatibility (`standalone` vs `consolidated`)
4. Time period compatibility (ISO `2023-04-01` to `2024-03-31`, quarter vs fiscal year)
5. Canonical unit compatibility (`INR` with `INR`, `pin codes` with `pin codes`)
6. Numeric variance type:
   - `EXACT_MATCH`: difference is $0.0$.
   - `ROUNDING_VARIANCE`: continuous percentage difference $\le 1.0\%$.
   - `MATERIAL_DIFFERENCE`: difference $> 1.0\%$ or any difference on discrete counts.
   - `NOT_COMPARABLE`: incompatible units or non-numeric comparison.
7. Vintage & estimation status:
   - Divergent projection/advance-estimate statuses evaluate to `LIKELY_CONTRADICTION`.

---

## 3. Detailed Walkthrough of the 4 Mandatory Cases

Every fact demonstrated below includes all required grounded fields: `subject`, `predicate`, `value`, `unit`, `period`, `scope`, `source document`, `page number`, `evidence text`, and `confidence`.

### Case 1: Cross-Document Numerical Corroboration

* **Fact A (Earnings Presentation):**
  * **Subject:** `Delhivery Limited`
  * **Predicate:** `revenue from operations`
  * **Value:** `8142`
  * **Unit:** `Cr` (normalized to `81,420,000,000.0 INR`)
  * **Period:** `FY2023-24` (`2023-04-01` to `2024-03-31`)
  * **Scope:** `consolidated`
  * **Source Document:** `03-delhivery-q4-fy24-earnings-presentation.pdf`
  * **Page Number:** `6`
  * **Evidence Text:** `"FY24 revenue from services stood at ₹8,142 Cr on a consolidated basis."`
  * **Confidence:** `0.95`

* **Fact B (Statutory Annual Report):**
  * **Subject:** `Delhivery Limited`
  * **Predicate:** `revenue from operations`
  * **Value:** `81415.38`
  * **Unit:** `million` (normalized to `81,415,380,000.0 INR`)
  * **Period:** `FY 2023-24` (`2023-04-01` to `2024-03-31`)
  * **Scope:** `consolidated`
  * **Source Document:** `02-delhivery-annual-report-fy24-excerpt.pdf`
  * **Page Number:** `22`
  * **Evidence Text:** `"The revenue from operations on consolidated basis for FY24 stood at ₹ 81,415.38 million as against ₹72,253.01 million for FY23"`
  * **Confidence:** `0.98`

* **Deterministic Comparison Features:**
  * `entity_match`: `True`
  * `predicate_match`: `True`
  * `period_match`: `EXACT`
  * `scope_match`: `EXACT`
  * `unit_match`: `True` (`INR` vs `INR`)
  * `numeric_variance_type`: `ROUNDING_VARIANCE`
  * `value_diff_percent`: `0.00567%`
  * `source_independence`: `True` (Presentation vs Audited Statutory Report)

* **Classification:** **`CORROBORATED`** (Confidence: `0.99`)
* **Grounded Explanation:** After normalization to a common canonical unit (`INR`), the values differ only by a small rounding variance (0.0057%), well within the 1.0% financial reporting tolerance. Both disclosures represent consolidated operations for the identical 12-month period FY2023-24.

---

### Case 2: Genuine & Likely Contradictions

The official assignment allows for genuine or likely contradictions. We demonstrate both:

#### 2A. Forecast & Vintage Divergence (`LIKELY_CONTRADICTION`)

* **Fact A (Economic Survey 2024-25):**
  * **Subject:** `India`
  * **Predicate:** `real GDP growth`
  * **Value:** `6.4`
  * **Unit:** `%` (canonical: `6.4 percent`)
  * **Period:** `FY2024/25` (`2024-04-01` to `2025-03-31`)
  * **Scope:** `national`
  * **Estimate Status:** `advance_estimate`
  * **Publication Date:** `July 2024`
  * **Source Document:** `01-india-economic-survey-2024-25-excerpt.pdf`
  * **Page Number:** `4`
  * **Evidence Text:** `"real GDP is estimated to grow by 6.4 per cent in FY25"`
  * **Confidence:** `0.95`

* **Fact B (IMF Article IV Consultation 2025):**
  * **Subject:** `India`
  * **Predicate:** `real GDP growth`
  * **Value:** `6.5`
  * **Unit:** `%` (canonical: `6.5 percent`)
  * **Period:** `FY2024/25` (`2024-04-01` to `2025-03-31`)
  * **Scope:** `national`
  * **Estimate Status:** `projection`
  * **Publication Date:** `January 2025`
  * **Source Document:** `03-imf-india-2025-article-iv-excerpt.pdf`
  * **Page Number:** `10`
  * **Evidence Text:** `"India's growth is projected at 6.5 percent in FY2024/25"`
  * **Confidence:** `0.95`

* **Deterministic Comparison Features:**
  * `entity_match`: `True`
  * `predicate_match`: `True`
  * `period_match`: `EXACT`
  * `scope_match`: `EXACT`
  * `numeric_variance_type`: `MATERIAL_DIFFERENCE` (Difference: `1.54%` $> 1.0\%$)
  * `estimate_match`: `DIVERGENT` (`advance_estimate` vs `projection`)

* **Classification:** **`LIKELY_CONTRADICTION`** (Confidence: `0.95`)
* **Grounded Explanation:** The Economic Survey reports 6.4% as a July 2024 advance estimate, whereas the IMF reports 6.5% as a January 2025 staff consultation projection. Both sources evaluate real GDP growth for the same FY2024/25 period, but the 0.1 percentage point divergence is explainable by differing publication vintages and forecasting methodologies.

#### 2B. Discrete Integer Count Contradiction (`CONTRADICTED`)

* **Fact A (Statutory Annual Report):**
  * **Subject:** `Delhivery Limited`
  * **Predicate:** `pin codes covered`
  * **Value:** `18793`
  * **Unit:** `pin codes` (canonical: `18793 pin codes`)
  * **Period:** `FY2023-24`
  * **Scope:** `national_network`
  * **Estimate Status:** `actual`
  * **Source Document:** `02-delhivery-annual-report-fy24-excerpt.pdf`
  * **Page Number:** `22`
  * **Evidence Text:** `"Express parcel delivery network reached 18,793 pin codes across India"`
  * **Confidence:** `0.98`

* **Fact B (Earnings Presentation):**
  * **Subject:** `Delhivery Limited`
  * **Predicate:** `pin codes covered`
  * **Value:** `18792`
  * **Unit:** `pin codes` (canonical: `18792 pin codes`)
  * **Period:** `FY2023-24`
  * **Scope:** `national_network`
  * **Estimate Status:** `actual`
  * **Source Document:** `03-delhivery-q4-fy24-earnings-presentation.pdf`
  * **Page Number:** `8`
  * **Evidence Text:** `"Covering 18,792 pin codes across India as of March 31, 2024"`
  * **Confidence:** `0.95`

* **Deterministic Comparison Features:**
  * `numeric_variance_type`: `MATERIAL_DIFFERENCE` (Discrete unit bypasses floating-point tolerance)
  * `value_diff_absolute`: `1.0 pin code`
  * `estimate_match`: `EXACT` (both are audited actual disclosures)

* **Classification:** **`CONTRADICTED`** (Confidence: `0.98`)
* **Grounded Explanation:** In discrete integer counting units (e.g. pin codes), a difference of 1 represents a material factual disagreement between disclosures for the identical network metric and financial year.

---

### Case 3: Contextual Difference (Preventing False Contradictions)

* **Fact A (Standalone Financials):**
  * **Subject:** `Delhivery Limited`
  * **Predicate:** `revenue from operations`
  * **Value:** `74540.82`
  * **Unit:** `million` (canonical: `74,540,820,000.0 INR`)
  * **Period:** `FY 2023-24`
  * **Scope:** `standalone`
  * **Source Document:** `02-delhivery-annual-report-fy24-excerpt.pdf`
  * **Page Number:** `22`
  * **Evidence Text:** `"The revenue from operations on standalone basis for FY24 stood at ₹ 74,540.82 million"`
  * **Confidence:** `0.95`

* **Fact B (Consolidated Financials):**
  * **Subject:** `Delhivery Limited`
  * **Predicate:** `revenue from operations`
  * **Value:** `81415.38`
  * **Unit:** `million` (canonical: `81,415,380,000.0 INR`)
  * **Period:** `FY 2023-24`
  * **Scope:** `consolidated`
  * **Source Document:** `02-delhivery-annual-report-fy24-excerpt.pdf`
  * **Page Number:** `22`
  * **Evidence Text:** `"The revenue from operations on consolidated basis for FY24 stood at ₹ 81,415.38 million"`
  * **Confidence:** `0.98`

* **Deterministic Comparison Features:**
  * `entity_match`: `True`
  * `predicate_match`: `True`
  * `period_match`: `EXACT`
  * `scope_match`: `DIFFERENT` (`standalone` $\ne$ `consolidated`)
  * `numeric_variance_type`: `MATERIAL_DIFFERENCE`

* **Classification:** **`CONTEXTUAL_DIFFERENCE`** (Confidence: `0.95`)
* **Grounded Explanation:** Demonstrates explicitly why naive numeric comparison produces a false contradiction. Both disclosures report revenue from operations for Delhivery Limited for FY2023-24. However, ₹74,540.82 million reflects only parent company standalone operations, while ₹81,415.38 million consolidates operating subsidiaries. Evaluating `scope_match` before value difference avoids falsely declaring a contradiction.

---

### Case 4: Real, Reproducible Extraction & Reasoning Failure

To fulfill Requirement #10, we reproduce a concrete failure from the starter dataset rather than presenting a hypothetical narrative.

* **Input:**
  * **Document:** `02-delhivery-annual-report-fy24-excerpt.pdf`
  * **Page:** `22` (Directors' Report — Financial Performance Table)
  * **Layout:** Multi-column comparative financial statement:
    ```
    Particulars              | Standalone – FY ended        | Consolidated – FY ended
                             | March 31, 2024 | March 31, 23 | March 31, 2024 | March 31, 23
    Revenue from Operations  | 74,540.82      | 66,586.61    | 81,415.38      | 72,253.01
    ```

* **Initial System Output (Naive 1D Text Extraction):**
  ```json
  {
    "subject": "Delhivery Limited",
    "predicate": "revenue from operations",
    "object_value": 74540.82,
    "unit": "million",
    "period": "FY 2023-24",
    "business_scope": "consolidated",
    "confidence": 0.85
  }
  ```

* **Failure:**
  The system extracted ₹74,540.82 million as **Consolidated** revenue. In reality, ₹74,540.82M is the **Standalone** revenue; Consolidated revenue is ₹81,415.38M. Downstream, when comparing against the Q4 Presentation disclosure of ₹8,142 Cr (Consolidated), the system would encounter an 8.44% discrepancy and falsely flag a contradiction.

* **Root Cause:**
  PyMuPDF plain text extraction (`get_text('text')`) streams lines in visual reading order, collapsing horizontal table columns into 1D sequential text:
  `Standalone – FY ended` $\to$ `Consolidated – FY ended` $\to$ `Revenue from Operations` $\to$ `74,540.82` $\to$ `66,586.61` $\to$ `81,415.38`.
  A single-pass LLM or naive chunker associating the most recent column header ("Consolidated") with the first numeric token in the row creates a cross-column scope misattribution.

* **Detection:**
  1. **Spatial Bounding Box Validation**: The numeric cell's horizontal center ($x_0 = 285\text{ pt}$) falls inside the Standalone column span ($x_0 = 240\text{ pt}, x_1 = 380\text{ pt}$), failing alignment with Consolidated ($x_0 = 420\text{ pt}$).
  2. **Discrepancy Diagnostics**: Cross-checking against presentation disclosure (₹8,142 Cr) triggers an 8.44% divergence on an audited statutory disclosure, penalizing scope confidence.

* **Current Mitigation:**
  `TableParser` in `core/table_parser.py` (via `pdfplumber`):
  - Detects explicit table vector rules and cell bounding boxes.
  - Reconstructs two-tier hierarchical headers (Parent: `Standalone` vs `Consolidated`, Child: `March 31, 2024`).
  - Assigns `business_scope = 'standalone'` directly from column hierarchy, classifying the pair as `CONTEXTUAL_DIFFERENCE`.

* **Future Improvement:**
  - Multimodal visual Document QA (e.g. LayoutLMv3 or ColPali) to preserve spatial 2D cell relations in borderless tables.
  - Cross-row accounting verification: Independent validator that verifies row totals and subsidiary eliminations across segment breakdowns.

*(To reproduce this failure demonstration in your terminal, run: `python scripts/reproduce_case4_failure.py`)*

---

## 4. Unseen Document Validation: Generalization Test

To satisfy Requirement #11, we generated an unseen regulatory document (`data/unseen_rbi_mpc_resolution.pdf`) representing the Reserve Bank of India Monetary Policy Committee Statement (August 8, 2024) and processed it through the normal pipeline without code modifications or special-casing.

### Measured Execution Metrics
* **Document Processed:** `data/unseen_rbi_mpc_resolution.pdf`
* **File Size:** 2,011 bytes
* **Pages Processed:** 2 pages
* **Processing Duration:** **0.25 seconds**
* **Facts Extracted:** 1 structured macroeconomic fact:
  ```json
  {
    "subject": "India",
    "predicate": "real GDP growth",
    "object_value": "7.2",
    "unit": "%",
    "canonical_value": 7.2,
    "canonical_unit": "percent",
    "period": "FY2024/25",
    "qualifiers": ["projection"],
    "confidence": 0.95,
    "document_name": "unseen_rbi_mpc_resolution.pdf",
    "page_number": 2,
    "evidence_id": "ev_doc_201d65451e_p2_b0"
  }
  ```
* **Evidence Items Stored:** 2 page evidence blocks with exact page coordinates
* **FAISS Vector Embeddings Generated:** 1 dense 384-dimensional vector indexed
* **Vector Similarity Retrieval Test:**
  Querying `"India real GDP growth"` returned the newly extracted fact `fact_888721782a` with a cosine similarity score of **`0.8816`**.

---

## 5. Test Suite & Verification Results

### 1. Pytest Execution
Command:
```bash
python -m pytest tests/
```
Output:
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\91630\Desktop\rag\fact-knowledge-layer
plugins: anyio-4.13.0, langsmith-0.8.5
collected 24 items

tests\test_api.py ....                                                   [ 16%]
tests\test_end_to_end.py .                                               [ 20%]
tests\test_entity_resolution.py ...                                      [ 33%]
tests\test_incremental.py ..                                             [ 41%]
tests\test_normalization.py ....                                         [ 58%]
tests\test_parser.py ...                                                 [ 70%]
tests\test_relationships.py .......                                      [100%]

======================= 24 passed, 1 warning in 11.88s ========================
```

### 2. Benchmark Evaluation Execution
Command:
```bash
python scripts/evaluate.py
```
Output:
```
================================================================================
FACT KNOWLEDGE LAYER - BENCHMARK EVALUATION REPORT
================================================================================
Total Samples Evaluated:      18
Overall Classification Acc:   100.00%
Macro F1 Score:               100.00%
FALSE CONTRADICTION RATE:     0.00% (CRITICAL DIAGNOSTIC)
================================================================================

PER-CLASS PERFORMANCE:
+-------------------------+-------------+----------+--------+-----------+
| Relationship Category   | Precision   | Recall   | F1     |   Support |
+=========================+=============+==========+========+===========+
| CORROBORATED            | 100.0%      | 100.0%   | 100.0% |         7 |
+-------------------------+-------------+----------+--------+-----------+
| CONTRADICTED            | 100.0%      | 100.0%   | 100.0% |         1 |
+-------------------------+-------------+----------+--------+-----------+
| LIKELY_CONTRADICTION    | 100.0%      | 100.0%   | 100.0% |         2 |
+-------------------------+-------------+----------+--------+-----------+
| CONTEXTUAL_DIFFERENCE   | 100.0%      | 100.0%   | 100.0% |         6 |
+-------------------------+-------------+----------+--------+-----------+
| UNCERTAIN               | 100.0%      | 100.0%   | 100.0% |         1 |
+-------------------------+-------------+----------+--------+-----------+
| RELATED_BUT_DIFFERENT   | 100.0%      | 100.0%   | 100.0% |         1 |
+-------------------------+-------------+----------+--------+-----------+
```

---

## 6. How to Run the Submission

### Quick Setup
```bash
# 1. Navigate to project root
cd c:/Users/91630/Desktop/rag/fact-knowledge-layer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Set GROQ_API_KEY in .env (if absent, offline fallback runs seamlessly)

# 4. Run the full test suite
python -m pytest tests/

# 5. Run the 18-sample benchmark
python scripts/evaluate.py

# 6. Run the Case 4 reproducible failure demonstration
python scripts/reproduce_case4_failure.py

# 7. Launch Streamlit Web UI
streamlit run app/ui.py
# (View at http://localhost:8501)

# 8. Launch FastAPI REST Backend
uvicorn app.api:app --reload --port 8000
# (View OpenAPI docs at http://localhost:8000/docs)
```
