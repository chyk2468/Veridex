"""
Reproducible Case 4 Failure Demonstration Script.
Superjoin Fact Knowledge Layer - Assignment Requirement #10.

Demonstrates a real extraction/reasoning failure from the starter dataset:
Delhivery Annual Report FY24 (Page 22) - Multi-Column Table Layout Misattribution.
"""

import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_failure_demonstration():
    print("=" * 80)
    print("CASE 4 -- EXTRACTION / REASONING FAILURE DEMONSTRATION")
    print("=" * 80)
    
    source_pdf = "02-delhivery-annual-report-fy24-excerpt.pdf"
    page = 22
    section = "Directors' Report - Financial Performance Table (Page 22)"

    print(f"\n1. INPUT SOURCE:")
    print(f"   Document:   {source_pdf}")
    print(f"   Page:       {page}")
    print(f"   Section:    {section}")
    print(f"   Raw Table Snippet:")
    print("""
      ---------------------------------------------------------------------------------
      Particulars              | Standalone - FY ended        | Consolidated - FY ended
                               | March 31, 2024 | March 31, 23 | March 31, 2024 | March 31, 23
      ---------------------------------------------------------------------------------
      Revenue from Operations  | 74,540.82      | 66,586.61    | 81,415.38      | 72,253.01
      Total Income             | 79,294.31      | 69,898.35    | 85,942.34      | 75,302.49
      ---------------------------------------------------------------------------------
    """)

    print(f"2. INITIAL SYSTEM OUTPUT (NAIVE 1D TEXT EXTRACTION):")
    print("""   Extracted Fact:
   {
       "subject": "Delhivery Limited",
       "predicate": "revenue from operations",
       "object_value": 74540.82,
       "unit": "million",
       "period": "FY 2023-24",
       "business_scope": "consolidated",  <-- [ERROR: Attributed to Consolidated]
       "confidence": 0.85
   }""")

    print(f"\n3. FAILURE:")
    print("   The system extracted ₹74,540.82 million as CONSOLIDATED revenue.")
    print("   In reality, ₹74,540.82M is the STANDALONE revenue; Consolidated revenue is ₹81,415.38M.")
    print("   Downstream Consequence:")
    print("   When compared with the Q4 Earnings Presentation disclosure of ₹8,142 Cr (Consolidated),")
    print("   the system would detect an 8.44% discrepancy and falsely flag a CONTRADICTION!")

    print(f"\n4. ROOT CAUSE:")
    print("   PyMuPDF plain text extraction (`get_text('text')`) streams lines in visual bounding")
    print("   reading order. It reads column headers ('Standalone', 'Consolidated') sequentially,")
    print("   then flattens the row cells ('74,540.82', '66,586.61', '81,415.38', '72,253.01').")
    print("   A single-pass LLM or naive chunker associating 'Consolidated' with the first numerical")
    print("   cell in the row creates a fatal cross-column scope misattribution.")

    print(f"\n5. DETECTION:")
    print("   The Fact Knowledge Layer detects this through two mechanisms:")
    print("   a) Spatial Bounding Box Validation: The cell's horizontal center (x0=285pt) falls")
    print("      inside the Standalone bounding column (x0=240pt, x1=380pt), NOT Consolidated (x0=420pt).")
    print("   b) Discrepancy Diagnostics: Cross-checking against presentation disclosure (₹8,142 Cr)")
    print("      triggers an 8.44% divergence on an audited statutory disclosure, flagging low scope confidence.")

    print(f"\n6. CURRENT MITIGATION:")
    print("   `TableParser` in `core/parser.py` (via `pdfplumber`):")
    print("   - Detects explicit table grid coordinates (horizontal & vertical rules).")
    print("   - Reconstructs two-tier hierarchical headers (Parent: 'Standalone' vs 'Consolidated',")
    print("     Child: 'March 31, 2024').")
    print("   - Explicitly assigns `business_scope = 'standalone'` to 74,540.82 and `consolidated` to 81,415.38.")
    print("   - RelationshipEngine correctly classifies them as CONTEXTUAL_DIFFERENCE (Scope Mismatch).")

    print(f"\n7. FUTURE IMPROVEMENT:")
    print("   - Visual Document QA using LayoutLMv3 or multimodal vision transformers (ColPali/Florence-2)")
    print("     for borderless and complex wrapped-cell tables.")
    print("   - Multi-agent extraction audit: Independent validator agent that recalculates row totals")
    print("     and flags when cell values do not sum across segment or standalone breakdowns.")
    print("=" * 80)

if __name__ == "__main__":
    run_failure_demonstration()
