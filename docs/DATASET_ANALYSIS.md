# Dataset Analysis & Inventory: Fact Knowledge Layer

This document contains the comprehensive inventory and structural analysis of the starter datasets provided for the **Superjoin VIT 2026 Engineering Intern Hiring Assignment**.

---

## 1. Overview of the Starter Datasets

The starter dataset comprises two distinct domains totaling 6 PDF documents across corporate disclosures and macro-institutional reports:
1. **Delhivery Corporate Disclosures** (`starter-datasets/delhivery/`): 3 documents covering financial, governance, network, and operational disclosures of Delhivery Limited.
2. **India Macroeconomic Reports** (`starter-datasets/india-macroeconomy/`): 3 institutional reports covering national accounts, inflation, growth forecasts, external accounts, and monetary indicators.

None of the facts, filenames, or metrics described below are hard-coded into the pipeline; they serve as ground truth for benchmarking, system calibration, and evaluation.

---

## 2. Document Inventory

| Domain | Filename | Page Count | Document Type | Primary Subject | Provenance & Excerpt Details |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Delhivery** | `01-delhivery-prospectus-2022-excerpt.pdf` | 100 pages | Initial Public Offering (IPO) Prospectus (May 2022) | Delhivery Limited (Corporate, History, Board, Restated Financials) | Curated excerpt retaining pages 1, 4, 26-37, 94-120, 216-245, 250-278. |
| **Delhivery** | `02-delhivery-annual-report-fy24-excerpt.pdf` | 100 pages | Integrated Annual Report (FY 2023-24) | Delhivery Limited (Financial Statements, Directors' Report, Governance) | Curated excerpt retaining pages 2-64, 105-141. |
| **Delhivery** | `03-delhivery-q4-fy24-earnings-presentation.pdf` | 27 pages | Investor & Earnings Presentation (May 2024) | Delhivery Limited (Q4 & Full Year FY24 Operational & Financial Highlights) | Complete filing retained (27 pages). |
| **Macroeconomy** | `01-india-economic-survey-2024-25-excerpt.pdf` | 89 pages | Ministry of Finance, Government of India Economic Survey 2024-25 | Indian Economy (State of Economy, External Sector, Prices & Inflation) | Curated excerpt retaining pages 4-6, 46-78, 124-176. |
| **Macroeconomy** | `02-rbi-annual-report-2024-25-excerpt.pdf` | 100 pages | Reserve Bank of India Annual Report 2024-25 | Indian Economy, Central Banking, Banking Stability, Inflation | Curated excerpt retaining pages 9-13, 27-111, 307-316. |
| **Macroeconomy** | `03-imf-india-2025-article-iv-excerpt.pdf` | 95 pages | IMF Article IV Consultation Staff Report (2025) | Indian Economy, Macroeconomic Surveillance, Medium-term Outlook | Curated excerpt retaining pages 1-95 (Press Release, Staff Report, Annexes). |

---

## 3. Deep Dive: Delhivery Dataset

### 3.1 Document 1: IPO Prospectus (2022)
- **Document Nature**: Statutory legal prospectus filed pursuant to SEBI ICDR Regulations.
- **Key Sections**: Prospectus Summary, Risk Factors, Capital Structure, Objects of the Offer, Summary Financial Statements, Management Team.
- **Key Numerical Facts**:
  - Fresh Issue Size: ₹40,000.00 million.
  - Offer for Sale (OFS) Size: ₹12,350.00 million.
  - Total Offer Size: ₹52,350.00 million.
  - Pre-Offer Shareholding of SVF Doorbell (Cayman) Ltd: 141,593,300 equity shares (22.04%).
  - Pre-Offer Shareholding of CA Swift Investments: 46,131,800 equity shares (7.18%).
  - Direct spend of Indian logistics sector (FY20): US$216 billion (projected to reach US$365 billion by FY26).
- **Key Semantic Facts**:
  - Registered Office: *N24-N34, S24-S34, Air Cargo Logistics Centre-II, Opposite Gate 6 Cargo Terminal, Indira Gandhi International Airport, New Delhi 110037, Delhi, India*.
  - Corporate Office: *Plot 5, Sector 44, Gurugram 122002, Haryana, India*.
  - Company Secretary & Compliance Officer: *Sunil Kumar Bansal*.
  - Key Executive Founders: *Sahil Barua (MD & CEO), Kapil Bharati (CTO), Suraj Saharan, Mohit Tandon*.

### 3.2 Document 2: Annual Report FY24
- **Document Nature**: Audited statutory annual report under Companies Act, 2013 and SEBI LODR.
- **Key Sections**: Directors' Report, Management Discussion & Analysis, Corporate Governance Report, Standalone & Consolidated Financial Statements.
- **Key Numerical Facts**:
  - Consolidated Revenue from Operations (FY24): **₹81,415.38 million** (vs ₹72,253.01 million in FY23).
  - Standalone Revenue from Operations (FY24): **₹1,679.68 million** (vs ₹8,123.02 million in FY23).
  - Pin Code Reach: Services provided in **18,793** postal index number ("PIN") codes out of 19,300 total in India.
  - Total Income (Consolidated FY24): ₹88,249.67 million.
  - Total Restated Loss / Loss after Tax: ₹(2,492.34) million (significant reduction from FY23 loss).
- **Key Semantic Facts**:
  - Sahil Barua: Managing Director & Chief Executive Officer (DIN: 05131571).
  - Kapil Bharati: Executive Director and Chief Technology Officer (DIN: 02227607).
  - Registered Office: Re-confirmed at Air Cargo Logistics Centre-II, IGI Airport, New Delhi.
  - Corporate Office: Re-confirmed at Plot No. 5, Sector 44, Gurugram, Haryana.

### 3.3 Document 3: Q4 FY24 Earnings Presentation
- **Document Nature**: Investor slide deck with non-GAAP operational and financial metrics.
- **Key Numerical Facts**:
  - Full Year FY24 Revenue: **₹8,142 Cr** (Crores).
  - Q4 FY24 Revenue: **₹2,076 Cr**.
  - Pin-code Reach: **18,792** Pin-codes covered (out of 19,300 Pin-codes as per India Post).
  - Adjusted EBITDA (FY24): ₹127 Cr (vs -₹68 Cr in FY23).
  - Express Parcel Shipments (FY24): 740 million shipments.
- **Key Semantic Facts**:
  - Full year EBITDA profitability achieved in FY24.
  - Part Truckload (PTL) volume expanded 30%+ YoY.

---

## 4. Deep Dive: India Macroeconomy Dataset

### 4.1 Document 1: India Economic Survey 2024-25
- **Subject**: Official Government of India macroeconomic review and survey.
- **Key Numerical Facts**:
  - Real GDP Growth FY25 (First Advance Estimates): **6.4 per cent**.
  - CPI Headline Inflation (FY25 H1): Softened to ~4.5 - 5.4 percent band.
  - Current Account Deficit (CAD) FY25: Well contained within 1.1 - 1.2% of GDP.
  - Agriculture sector growth: Projected at 3.5 - 4.0% recovery.

### 4.2 Document 2: RBI Annual Report 2024-25
- **Subject**: Central bank monetary policy, banking supervision, economic review.
- **Key Numerical Facts**:
  - Real GDP Growth Q1 2024-25: **6.5 per cent** (quarterly actual).
  - Real GDP Growth Q2 2024-25: **5.6 per cent**.
  - Real GDP Growth FY26 (2025-26) Projection: **6.5 per cent**.
  - Headline CPI Inflation (2024-25): Eased to 4.6 per cent.
  - Foreign Exchange Reserves: Over **US$ 650 billion** (peaked near US$ 651.4 billion).

### 4.3 Document 3: IMF Article IV Consultation 2025
- **Subject**: International multilateral economic surveillance report.
- **Key Numerical Facts**:
  - Real GDP Growth FY2024/25: **6.5 percent** (IMF reported full-year figure).
  - Real GDP Growth Q1 FY2025/26 (2025Q2): **7.8 percent**.
  - Real GDP Growth FY2025/26 Baseline Projection: **6.6 percent** (moderating to 6.2% over medium term).
  - Headline Inflation (Sept 2024): 1.5 percent; FY projection 3.5 percent converging to 4.0 percent.
  - Foreign Exchange Reserves: US$ 650 billion.

---

## 5. Overlapping Facts & The Four Mandatory Cases

### Case 1: Corroboration Across Independent Documents
1. **Delhivery FY24 Consolidated Revenue**:
   - Document A: `03-delhivery-q4-fy24-earnings-presentation.pdf` (Page 6): `"Revenue: ₹8,142 Cr"`.
   - Document B: `02-delhivery-annual-report-fy24-excerpt.pdf` (Page 22): `"The revenue from operations on consolidated basis for FY24 stood at ₹ 81,415.38 million"`.
   - *Grounding & Normalization*:
     - ₹8,142 Cr = ₹81,420 Million = ₹81,420,000,000 INR.
     - ₹81,415.38 Million = ₹81,415,380,000 INR.
     - Difference: ₹4.62 million out of ₹81,415 million ($0.005\%$), well within reporting rounding tolerance.
     - Both refer to Subject: `Delhivery Limited`, Predicate: `revenue from operations`, Period: `FY 2023-24`, Scope: `consolidated`.
   - *Classification*: **CORROBORATED**.

2. **India Total Pin Code Universe**:
   - Document A: `02-delhivery-annual-report-fy24-excerpt.pdf` (Page 7): `"the 19,300 pin codes in India"`.
   - Document B: `03-delhivery-q4-fy24-earnings-presentation.pdf` (Page 8): `"19,300 Pin-codes as per India Post"`.
   - *Classification*: **CORROBORATED**.

### Case 2: Genuine Contradiction
1. **India Real GDP Growth for FY2024/25**:
   - Document A: `01-india-economic-survey-2024-25-excerpt.pdf` (Page 4): `"India’s real GDP is estimated to grow by 6.4 per cent in FY25."`
   - Document B: `03-imf-india-2025-article-iv-excerpt.pdf` (Page 10): `"India’s real GDP grew by 6.5 percent in FY2024/25."`
   - *Conflict*: Same subject (`India`), same metric (`Real GDP growth`), same period (`FY2024/25`), same scope (`National`), but mutually incompatible values (`6.4%` vs `6.5%`).
   - *Classification*: **CONTRADICTED**.

2. **India Real GDP Growth Projection for FY2025/26**:
   - Document A: `02-rbi-annual-report-2024-25-excerpt.pdf` (Page 17): `"real GDP growth for 2025-26 is projected at 6.5 per cent"`.
   - Document B: `03-imf-india-2025-article-iv-excerpt.pdf` (Page 13): `"real GDP growth is projected at 6.6 percent in FY2025/26"`.
   - *Conflict*: 6.5% (RBI) vs 6.6% (IMF).
   - *Classification*: **CONTRADICTED**.

### Case 3: Apparent Contradiction Explained by Context
1. **Delhivery FY24 Revenue: Standalone vs Consolidated**:
   - Fact A: `02-delhivery-annual-report-fy24-excerpt.pdf` (Page 22): `"The revenue from operations on standalone basis for FY24 stood at ₹ 1,679.68 million"`.
   - Fact B: `03-delhivery-q4-fy24-earnings-presentation.pdf` (Page 6): `"Revenue: ₹8,142 Cr"` (Consolidated).
   - *Resolution*: Naive comparison suggests an 50x contradiction (`₹1,679.68M` vs `₹81,420M`). However, deterministic feature comparison detects `accounting_scope` mismatch: Fact A is `standalone` (excluding subsidiaries like SpotOn Logistics), while Fact B is `consolidated`.
   - *Classification*: **CONTEXTUAL_DIFFERENCE** (Accounting Scope).

2. **India Real GDP Growth: Q1 vs Full Year**:
   - Fact A: `02-rbi-annual-report-2024-25-excerpt.pdf` (Page 24): `"real GDP rose (y-o-y) by 6.5 per cent in Q1:2024-25"`.
   - Fact B: `03-imf-india-2025-article-iv-excerpt.pdf` (Page 3): `"real GDP expanded by 7.8 percent in the first quarter of FY2025/26"`.
   - *Resolution*: Both are first-quarter growth rates, but Fact A represents `Q1 FY2024/25` while Fact B represents `Q1 FY2025/26`.
   - *Classification*: **CONTEXTUAL_DIFFERENCE** (Reporting Period).

### Case 4: Real Extraction / Reasoning Failure
1. **Multi-Column Financial Statement Tabular Misalignment**:
   - *Problem*: In `02-delhivery-annual-report-fy24-excerpt.pdf` Page 22, the table contains adjacent columns for FY24 and FY23:
     `Revenue from Operations: FY24 = 81,415.38 | FY23 = 72,253.01`. Naive OCR or line-by-line text extraction often flattens this text into `Revenue from Operations 81,415.38 72,253.01`, causing the parser to associate `72,253.01` with `FY24` or lose the period entirely.
   - *Consequence*: If assigned to FY24, it creates a severe false contradiction against the presentation's `₹8,142 Cr`.
   - *Handling in our Architecture*: The `TableParser` uses cell bounding boxes and explicit header propagation across columns, while the `Fact` schema validates period boundaries and marks unanchored cells with `REVIEW_REQUIRED` / extraction uncertainty.

---

## 6. Extraction Challenges Identified
1. **Unit Multipliers**: Indian documents alternate between `Crores (₹ Cr)`, `Lakhs`, and `Millions (₹ million)`. Without canonical normalization, numeric comparison is impossible.
2. **Fiscal Year Conventions**: Documents use `FY24`, `FY2023-24`, `2023-24`, `FY2024/25`. Canonical intervals (start date, end date, fiscal year) are essential.
3. **Footnotes and Qualifiers**: Critical conditions like `*pro forma basis`, `Adjusted EBITDA`, and `standalone` often reside in footnotes or column headers.
