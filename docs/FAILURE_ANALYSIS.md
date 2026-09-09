# Fact Knowledge Layer — Extraction & Reasoning Failure Analysis

## 1. Overview

In production document understanding systems, failures rarely occur due to complete lack of knowledge. Rather, they occur at the boundaries: complex table layouts, subtle accounting qualifiers, unit mismatches, and over-generalizing heuristics.

This document provides an in-depth audit of four primary failure modes encountered when processing corporate disclosures and macroeconomic reports, documenting:
1. **What went wrong** (with concrete examples).
2. **The root cause** in parsing, extraction, or reasoning.
3. **How the system flags the failure** (confidence penalties, schema checks).
4. **How the system mitigates or resolves the failure**.

---

## 2. Failure Mode 1: Multi-Column Table Cell-to-Header Misattribution

### Concrete Example
In Delhivery's Annual Report FY24 (`02-delhivery-annual-report-fy24-excerpt.pdf`, Page 22), the Statement of Profit and Loss presents Standalone and Consolidated figures in adjacent vertical columns:

| Particulars | Note | Standalone FY24 | Standalone FY23 | Consolidated FY24 | Consolidated FY23 |
|---|:---:|:---:|:---:|:---:|:---:|
| **Revenue from operations** | 24 | **₹ 74,540.82** | ₹ 50,000.00 | **₹ 81,415.38** | ₹ 72,253.00 |

### What Went Wrong
A naive PDF parser extracting text line-by-line produces:
`Revenue from operations 24 ₹ 74,540.82 ₹ 50,000.00 ₹ 81,415.38 ₹ 72,253.00`
A standard LLM given this line often pairs the label *"Revenue from operations"* with the first number it encounters (`74,540.82`) while assigning it the global document title (*"Consolidated Financial Statements"*). This results in a fact claiming that **Consolidated** revenue was ₹74,540.82 million, which directly contradicts the presentation's ₹8,142 Cr (₹81,420M).

### Root Cause
- **Visual vs Reading Order Gap**: PyMuPDF block extraction clusters text based on vertical spacing, flattening horizontal table columns into interleaved strings unless table bounding geometry is analyzed.
- **Header Column Span Misalignment**: Multi-tier headers (e.g. *"Standalone"* spanning columns 3-4, *"Consolidated"* spanning columns 5-6) are stripped of hierarchical relationships in plain text conversion.

### How the System Flags It
1. **Coordinate Verification**: The system verifies whether the bounding box x-coordinate of the value cell falls within the x-interval of the claimed header `[x0_header, x1_header]`.
2. **Confidence Penalty**: When a cell's horizontal center does not align with the parent column header by more than 15pt, the extraction confidence score is downgraded from `0.95` to `< 0.60`.
3. **Validation Error**: If confidence drops below `settings.CONFIDENCE_THRESHOLD` (0.70), the fact status is flagged as `"unverified_layout"`.

### How the System Mitigates It
- **Structural Table Extraction (`core/table_parser.py`)**: The system uses `pdfplumber` to detect explicit horizontal and vertical vector lines.
- **Hierarchical Column Inheritance**: Each cell is explicitly mapped to its enclosing column header. `business_scope` is explicitly populated as `"standalone"` or `"consolidated"` from the column header metadata rather than inferred from the row label.

---

## 3. Failure Mode 2: Accounting Qualifier and Restatement Omission

### Concrete Example
In the RBI Annual Report 2024-25 (`02-rbi-annual-report-2024-25-excerpt.pdf`, Page 17), headline CPI inflation is disclosed in two distinct tables:
- Table A (Historical Actuals): `Headline CPI inflation: 5.4% (FY24)`
- Table B (Monetary Policy Projections): `Headline CPI inflation: 4.5% (FY25 projected, baseline scenario without unseasonal food shocks)`

Furthermore, prior-year figures in statutory reports often carry footnote qualifiers such as:
`"Revenue from operations for FY23: ₹ 72,253.00 million (Restated for Scheme of Amalgamation)"`.

### What Went Wrong
Standard (Subject, Predicate, Object) fact extraction models discard parentheticals, notes, and qualifiers. If the qualifier *"projected"* or *"restated"* is stripped, the system stores:
- Fact A: `India | headline CPI inflation | 5.4% | FY24`
- Fact B: `India | headline CPI inflation | 4.5% | FY24 (originally FY25 projection, but period conflated)`
This triggers a false contradiction alert between actual inflation and projected inflation.

### Root Cause
- **LLM Triplet Bias**: Prompting LLMs to extract triplets (`subject`, `predicate`, `value`) implicitly trains the model to drop "extraneous" descriptive qualifiers to fit JSON schema constraints.
- **Footnote Disconnection**: Footnotes appear at the bottom of the page (e.g. 500pt below the table). A standard sliding window chunker may include the table in Chunk 1 and the footnote in Chunk 2, breaking the link.

### How the System Flags It
1. **Schema Enforcement**: The `Fact` model includes an explicit `qualifiers: List[str]` field.
2. **Qualifier Conflict Check**: `RelationshipEngine` compares qualifiers between facts:
   - If Fact A has `qualifiers = ["restated"]` and Fact B has `qualifiers = ["as originally reported"]`, `scope_match` is flagged as `DIFFERENT`.

### How the System Mitigates It
- **Proximity Footnote Extraction**: In `core/chunker.py`, when a table evidence block contains footnote markers (`*`, `(1)`, `Note`), any text blocks located within 60pt of the bottom margin on that page are merged into the context window.
- **Decision Engine Branching**: If qualifiers indicate restatements or differing accounting bases (e.g. *pro-forma* vs *statutory*), the engine classifies the relationship as `CONTEXTUAL_DIFFERENCE` with a grounded explanation explaining the restatement.

---

## 4. Failure Mode 3: Continuous Percentage Tolerance Applied to Discrete Counts

### Concrete Example
- **Prospectus 2022**: Delhivery network reach is stated as **18,793 pin codes** covered across India.
- **Competitor / Third-Party Analysis**: Claims Delhivery covers **18,792 pin codes**.

### What Went Wrong
If a system applies a standard financial rounding tolerance ($\le 1.0\%$) uniformly across all numerical metrics:
$$\text{Difference} = \frac{|18,793 - 18,792|}{18,793} \times 100 = 0.0053\%$$
Since $0.0053\% \le 1.0\%$, the system would classify this pair as **`CORROBORATED`**.
However, in network logistics, pin codes are discrete integer entities. Covering 18,793 pin codes is an exact audit claim; missing a pin code is an actual discrepancy or error.

### Root Cause
- **Type Agnosticism**: Treating all numbers as dimensionless floats without semantic unit classification.
- **Uniform Tolerance Policy**: Using a single global epsilon across currencies, percentages, ratios, and discrete counts.

### How the System Flags It
- **Unit Classification**: The `Normalizer` assigns semantic types:
  - Currencies $\to$ `value_type="currency"`
  - Percentages $\to$ `value_type="percentage"`
  - Counts $\to$ `canonical_unit in ("pin codes", "count", "units", "facilities")`
- **Zero-Tolerance Warning**: Whenever `canonical_unit` is a counting unit, the engine flags `tolerance_mode = "EXACT_INTEGER"`.

### How the System Mitigates It
In `core/relationship.py` (lines 85-88):
```python
if (fact_a.canonical_unit or "").lower() in ("pin codes", "count") or (fact_b.canonical_unit or "").lower() in ("pin codes", "count"):
    # Discrete counts cannot use continuous percentage tolerances
    val_match = "AGREES" if val_diff_pct == 0.0 else "DISAGREES"
```
Because $18,793 \ne 18,792$, `val_match` evaluates to `DISAGREES`, and the engine correctly classifies the pair as **`CONTRADICTED`**.

---

## 5. Failure Mode 4: Ambiguous Time Horizons and Overlapping Periods

### Concrete Example
- Economic Survey reports: `India real GDP growth for FY2024/25: 6.4%`
- IMF Article IV reports: `India real GDP growth for CY2024: 7.0%`

### What Went Wrong
Both sources discuss India real GDP growth during the year 2024. A naive period matcher that simply checks for the substring `"2024"` assumes they are discussing the identical time period and flags a severe contradiction ($6.4\% \ne 7.0\%$).

### Root Cause
- **Calendar Year vs Fiscal Year Conflation**: India's Fiscal Year runs from April 1 to March 31 (`2024-04-01` to `2025-03-31`), whereas a Calendar Year runs from January 1 to December 31 (`2024-01-01` to `2024-12-31`). They overlap by 9 months but differ by 3 months.

### How the System Mitigates It
- **Canonical Date Interval Modeling (`models/fact.py`)**: Every period is converted into concrete ISO date intervals:
  - `Period(label="FY2024/25", start_date="2024-04-01", end_date="2025-03-31")`
  - `Period(label="CY2024", start_date="2024-01-01", end_date="2024-12-31")`
- **Period Overlap Logic**:
  - `is_exact_match()`: Returns `False`.
  - `overlaps()`: Returns `True`.
  - `period_match` is evaluated as `"OVERLAPPING"`.
- **Classification**: Because periods are overlapping but not identical, differing values are classified as **`CONTEXTUAL_DIFFERENCE`**, preventing a false contradiction.
