# Fact Knowledge Layer

> **Superjoin VIT 2026 Engineering Intern Hiring Assignment Submission**  
> *A Production-Grade, Explainable, Generalized Knowledge Layer for Grounded Cross-Document Fact Intelligence.*

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python)](https://www.python.org/)
[![Tests Passing](https://img.shields.io/badge/Pytest-22%20Passed%20(100%25)-10B981.svg)](https://docs.pytest.org/)
[![Benchmark Accuracy](https://img.shields.io/badge/Benchmark%20Accuracy-100.00%25-10B981.svg)](docs/EVALUATION.md)
[![False Contradiction Rate](https://img.shields.io/badge/False%20Contradiction%20Rate-0.00%25-10B981.svg)](docs/EVALUATION.md)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B.svg?logo=streamlit)](https://streamlit.io/)

---

## 1. Executive Summary & Philosophy

Most AI document systems build generic "PDF chatbots" that dump chunked text into an LLM context window. When asked to compare figures across documents, LLMs routinely hallucinate, stumble over unit discrepancies, and falsely flag contradictions between numbers that actually agree or differ by accounting scope.

The **Fact Knowledge Layer** takes an engineering-first, explainable approach:
1. **Facts as First-Class Entities**: Extracts structured `Fact` objects with explicit subject entities, predicates, normalized numeric values, canonical units, ISO date intervals, and accounting scopes.
2. **Every Claim Grounded in Evidence**: Every fact retains 1-indexed PDF page numbers, exact text bounding box coordinates `[x0, y0, x1, y1]`, and verbatim source quotes.
3. **RULE 2 — Deterministic Relationship Logic**: **The LLM does NOT classify relationships.** Python deterministically normalizes values, resolves units, and evaluates a 7-feature comparative matrix (`entity_match`, `predicate_match`, `period_match`, `scope_match`, `unit_match`, `value_match`, `source_independence`).
4. **Zero Hallucination Explanations**: Groq (`llama-3.3-70b-versatile`) is invoked solely to synthesize natural language explanations constrained strictly to the deterministic feature matrix and verbatim evidence snippets.

---

## 2. System Architecture

```mermaid
graph TD
    A[Raw PDF Documents] --> B[PyMuPDF Text & Coordinate Parser]
    A --> C[pdfplumber Structural Table Parser]
    B --> D[Evidence Blocks with Bounding Boxes]
    C --> D
    D --> E[Candidate Fact Detector & Sliding Chunker]
    E --> F[LLM Fact Extractor: Groq Llama-3.3-70b / Offline Fallback]
    F --> G[Deterministic Normalizer: Currency, Multipliers, Periods]
    G --> H[Entity & Predicate Resolver]
    H --> I[(SQLite Relational Knowledge Store)]
    H --> J[FAISS Vector Store: 384-dim all-MiniLM-L6-v2]
    I --> K[Candidate Matcher: Vector + Lexical Pruning]
    J --> K
    K --> L[Deterministic Relationship Engine: Rule 2 Python Logic]
    L --> M[Comparison Features: Entity, Predicate, Period, Scope, Unit, Value Diff]
    M --> N[Classification: CORROBORATED, CONTRADICTED, CONTEXTUAL_DIFF, UNCERTAIN]
    N --> O[LLM Grounded Explanation Engine]
    O --> P[FastAPI REST Backend]
    P --> Q[Streamlit Interactive Explorer UI]
```

### Architectural Highlights
- **Page-Aware Parser (`core/parser.py`)**: Traverses PDFs page-by-page with PyMuPDF, preserving exact coordinates and computing SHA-256 hashes for idempotent, duplicate-free ingestion.
- **Table Parser (`core/table_parser.py`)**: Uses `pdfplumber` to extract grid cells, ensuring multi-column values retain their column hierarchy (e.g. Standalone vs Consolidated).
- **Deterministic Normalizer (`core/normalizer.py`)**: Converts currency strings (`₹`, `Rs`, `INR`, `$`, `USD`), multiplier suffixes (`Cr`, `Lakh`, `Million`, `Billion`, `k`), parenthetical negatives (`(2,492)`), percentages, and fiscal year/quarter labels (`FY24` -> `2023-04-01` to `2024-03-31`) into canonical base types with zero LLM arithmetic calls.
- **Entity Resolver (`core/entity_resolver.py`)**: Strips legal corporate suffixes (`Delhivery Ltd.` -> `Delhivery Limited`) and standardizes sovereign aliases (`Republic of India` -> `India`).
- **Vector Retrieval (`retrieval/vector_store.py`)**: Dense vector indexing with FAISS `IndexFlatIP` and sentence-transformers (`all-MiniLM-L6-v2`), with an automated NumPy cosine fallback.
- **Deterministic Engine (`core/relationship.py`)**: Rule-based classification engine establishing `CORROBORATED`, `CONTRADICTED`, `CONTEXTUAL_DIFFERENCE`, `RELATED_BUT_DIFFERENT`, and `UNCERTAIN`.

For full architecture details and design trade-offs (SQLite vs Postgres, FAISS vs dedicated Vector DB), see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 3. The 4 Mandatory Demonstration Cases

The system specifically showcases the four demonstration cases required by the assignment:

### 🌟 Case 1: Cross-Document Numerical Corroboration
- **Source A:** `03-delhivery-q4-fy24-earnings-presentation.pdf` (Page 6)
  - Raw Claim: `"FY24 revenue from services stood at ₹8,142 Cr on a consolidated basis."`
  - Normalized: `81,420,000,000.0 INR`, Period: `FY2023/24`, Scope: `consolidated`
- **Source B:** `02-delhivery-annual-report-fy24-excerpt.pdf` (Page 22)
  - Raw Claim: `"Revenue from operations for the financial year 2023-24 stood at ₹ 81,415.38 million."`
  - Normalized: `81,415,380,000.0 INR`, Period: `FY2023/24`, Scope: `consolidated`
- **Deterministic Features:**
  - `entity_match`: True | `predicate_match`: True | `period_match`: EXACT | `scope_match`: EXACT
  - `value_match`: TOLERANCE_MATCH (Percentage variance: **0.0057%** $\le$ 1.0% financial threshold)
- **Outcome:** Classified as **`CORROBORATED`** (Confidence: 0.99).
- **Grounded Explanation:** Delhivery Limited's revenue from operations for FY2023-24 reported as ₹8,142 Cr in the Earnings Presentation corresponds to ₹81,420 million. This agrees with ₹81,415.38 million in the Annual Report within a rounding variance of 0.0057%. Both figures reflect consolidated operations over identical 12-month periods.

---

### 🚨 Case 2: Genuine Macroeconomic Contradiction
- **Source A:** `01-india-economic-survey-2024-25-excerpt.pdf` (Page 4)
  - Raw Claim: `"Real GDP is estimated to grow by 6.4 per cent in FY25."`
  - Normalized: `6.4%`, Subject: `India`, Predicate: `real GDP growth`, Period: `FY2024/25`
- **Source B:** `03-imf-india-2025-article-iv-excerpt.pdf` (Page 6)
  - Raw Claim: `"India’s growth is projected at 6.5 percent in FY2024/25."`
  - Normalized: `6.5%`, Subject: `India`, Predicate: `real GDP growth`, Period: `FY2024/25`
- **Deterministic Features:**
  - `entity_match`: True (`India`) | `predicate_match`: True (`real GDP growth`)
  - `period_match`: EXACT (`FY2024/25`) | `scope_match`: EXACT
  - `value_match`: DISAGREES (Variance: **1.54%** $>$ 1.0% tolerance)
- **Outcome:** Classified as **`CONTRADICTED`** (Confidence: 0.96).
- **Grounded Explanation:** Direct macroeconomic contradiction for India real GDP growth during FY2024/25. The Economic Survey estimates 6.4%, while the IMF projects 6.5%. Both sources refer to the exact same sovereign entity, metric, and fiscal period, but report conflicting economic estimates exceeding allowable tolerance.

---

### ⚖️ Case 3: Contextual Difference (Not a Contradiction)
- **Source A:** `02-delhivery-annual-report-fy24-excerpt.pdf` (Page 22)
  - Standalone P&L: `"Revenue from operations on standalone basis for FY24 stood at ₹ 74,540.82 million."`
  - Scope: `standalone`
- **Source B:** `02-delhivery-annual-report-fy24-excerpt.pdf` (Page 22)
  - Consolidated P&L: `"Revenue from operations on consolidated basis for FY24 stood at ₹ 81,415.38 million."`
  - Scope: `consolidated`
- **Deterministic Features:**
  - `entity_match`: True | `predicate_match`: True | `period_match`: EXACT
  - `scope_match`: **DIFFERENT** (`standalone` $\ne$ `consolidated`)
- **Outcome:** Classified as **`CONTEXTUAL_DIFFERENCE`** (Confidence: 0.95).
- **Grounded Explanation:** While both numbers represent Delhivery's FY24 revenue, they differ by accounting scope. ₹74,540.82 million captures only standalone entity operations, whereas ₹81,415.38 million incorporates all operating subsidiaries. The system correctly isolates scope divergence, preventing a false contradiction.
- *(Also demonstrated: Q4 FY24 ₹2,076 Cr vs Full Year FY24 ₹8,142 Cr, classified as `CONTEXTUAL_DIFFERENCE` due to `period_match: OVERLAPPING`).*

---

### ⚠️ Case 4: Extraction & Reasoning Failure Analysis
Comprehensive documentation of real-world document intelligence failure modes:
1. **Multi-Column Table Layout**: Cell-to-header misattribution in side-by-side standalone vs consolidated balance sheets. Flagged by bounding box x-coordinate misalignment; mitigated by `TableParser` grid column reconstruction.
2. **Accounting Qualifier Omission**: Dropping *"restated"* or *"pro-forma"* parentheticals. Flagged by the explicit `qualifiers` model field; mitigated by table footnote proximity chunking and `CONTEXTUAL_DIFFERENCE` branching.
3. **Discrete Count vs Continuous Tolerance**: Erroneously applying a continuous percentage tolerance ($\le 1.0\%$) to integer counts (e.g. `18,793` vs `18,792` pin codes). Flagged by semantic unit typing; mitigated by unit-specific exact integer equality logic.

For complete root cause analyses and detection diagnostics, see [docs/FAILURE_ANALYSIS.md](docs/FAILURE_ANALYSIS.md).

---

## 4. Benchmark & Diagnostic Evaluation

Evaluated across an 18-sample ground truth dataset extracted from the starter PDFs:

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
| CONTRADICTED            | 100.0%      | 100.0%   | 100.0% |         3 |
+-------------------------+-------------+----------+--------+-----------+
| CONTEXTUAL_DIFFERENCE   | 100.0%      | 100.0%   | 100.0% |         6 |
+-------------------------+-------------+----------+--------+-----------+
| UNCERTAIN               | 100.0%      | 100.0%   | 100.0% |         1 |
+-------------------------+-------------+----------+--------+-----------+
| RELATED_BUT_DIFFERENT   | 100.0%      | 100.0%   | 100.0% |         1 |
+-------------------------+-------------+----------+--------+-----------+
```

To run the benchmark locally:
```bash
python scripts/evaluate.py
```
For full details, see [docs/EVALUATION.md](docs/EVALUATION.md).

---

## 5. Quickstart & Installation

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Git

### 1. Clone & Navigate
```bash
git clone https://github.com/your-username/fact-knowledge-layer.git
cd fact-knowledge-layer
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy the template and configure your Groq API key:
```bash
cp .env.example .env
```
In `.env`:
```ini
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```
*(Note: If no API key is provided, the system automatically runs in offline heuristic fallback mode with 100% test pass capability!)*

### 4. Launch the Interactive Streamlit UI
```bash
streamlit run app/ui.py
```
Open your browser at `http://localhost:8501`.

### 5. Launch the FastAPI REST API
```bash
uvicorn app.api:app --reload --port 8000
```
Interactive OpenAPI documentation available at `http://localhost:8000/docs`.

### 6. Run CLI Ingestion on Any PDF
```bash
python scripts/ingest.py path/to/document.pdf
```

### 7. Run Complete Pytest Suite
```bash
python -m pytest tests/
```

---

## 6. Docker Deployment

Deploy both the FastAPI REST backend and Streamlit UI in isolated containers:

```bash
docker-compose up --build
```
- Streamlit UI: `http://localhost:8501`
- FastAPI Docs: `http://localhost:8000/docs`

---

## 7. REST API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | Health check verifying database and LLM provider status. |
| `/statistics` | `GET` | Aggregated count of documents, facts, and relationships. |
| `/cases` | `GET` | Returns the 4 mandatory assignment demonstration cases. |
| `/documents/upload` | `POST` | Upload and auto-ingest a PDF document. |
| `/documents` | `GET` | List all ingested documents with page counts and status. |
| `/documents/{id}` | `GET` | Retrieve detailed document metadata and pages. |
| `/facts` | `GET` | Query indexed facts with subject, predicate, and scope filters. |
| `/facts/{id}` | `GET` | Get single fact with linked evidence snippet and coordinates. |
| `/facts/{id}/relationships` | `GET` | Retrieve all relationships involving a specific fact. |
| `/relationships` | `GET` | List relationships filtered by type and minimum confidence. |
| `/relationships/{id}` | `GET` | Inspect pair with comparison features and explanation. |
| `/search` | `GET` | Semantic and keyword vector search over indexed facts. |

---

## 8. 3-Minute Video Demo Script

Follow this script to record a concise, high-impact 3-minute demonstration:

- **[0:00 - 0:30] Introduction & Core Problem**
  - Show the Streamlit UI dashboard.
  - Explain why standard RAG chatbots fail on financial & economic PDFs: they hallucinate numbers, misinterpret currencies, and accuse documents of contradicting when one is Standalone and one is Consolidated.
  - Introduce the core architectural principle: **Facts as first-class entities + Rule 2 (Deterministic Relationship Engine)**.
- **[0:30 - 1:15] Case 1 & Case 2 Live Inspection**
  - Click on **Tab 1 ("🌟 The 4 Mandatory Cases")**.
  - Show **Case 1 (Corroboration)**: Highlight ₹8,142 Cr vs ₹81,415.38 million. Point out the canonical normalized values, the 0.0057% difference calculation, the page citations, and the grounded explanation.
  - Show **Case 2 (Contradiction)**: Highlight India Real GDP Growth (6.4% Economic Survey vs 6.5% IMF). Point out identical entity, predicate, and fiscal year period, triggering a genuine contradiction.
- **[1:15 - 2:00] Case 3 & Case 4 Live Inspection**
  - Show **Case 3 (Contextual Difference)**: Highlight Standalone vs Consolidated revenue. Emphasize that the engine checks scope *before* value, achieving a **0.00% False Contradiction Rate**.
  - Expand **Case 4 (Failure Analysis)**: Walk through multi-column table layout cell-to-header misattribution and discrete count tolerances.
- **[2:00 - 2:30] Interactive Fact Search & Document Ingestion**
  - Switch to **Tab 2 ("🔍 Fact Explorer & Search")**. Type `"Delhivery revenue"` or `"pin codes"` in the search bar. Show instant vector similarity search, exact PDF page numbers, and bounding box coordinates.
  - In the sidebar, drag and drop an unseen PDF (or click the quick-ingest button). Show instant parsing, fact extraction, and cross-document relationship discovery in seconds.
- **[2:30 - 3:00] Benchmark Diagnostics & Conclusion**
  - Switch to **Tab 5 ("📊 Benchmark & Diagnostics")**.
  - Show the real-time terminal/UI benchmark: **100% Accuracy, 0.00% False Contradiction Rate across all 18 samples**.
  - Highlight the 22 passing unit/integration tests and conclude.

---

## 9. Submission Checklist

- [x] Grounded evidence extraction with 1-indexed page preservation and block bounding boxes.
- [x] Deterministic normalization engine for currencies, Indian/Western multipliers, and fiscal periods.
- [x] Rule 2 strictly implemented: LLM does NOT classify relationships; Python evaluates deterministic features.
- [x] Grounded natural-language explanations constrained strictly to the evidence.
- [x] All 4 mandatory demonstration cases fully built and interactive in UI and API.
- [x] 18-sample ground-truth benchmark with **100.00% Accuracy** and **0.00% False Contradiction Rate**.
- [x] Incremental processing with SHA-256 hash deduplication.
- [x] Generalization verified on unseen regulatory disclosures.
- [x] 22 Pytest unit and integration tests passing.
- [x] Production FastAPI backend and modern Streamlit frontend.
- [x] Complete architectural documentation, evaluation report, failure analysis, Dockerfile, and video script.
