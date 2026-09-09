"""
Generate an unseen test PDF: RBI Monetary Policy Committee Statement.
Used to evaluate the system's ability to generalize to new, unseen regulatory and economic disclosures
without hardcoded templates or overfitted patterns.
"""

import sys
from pathlib import Path
import fitz  # PyMuPDF

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PDF = REPO_ROOT / "data" / "unseen_rbi_mpc_resolution.pdf"

def generate_unseen_pdf():
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()

    # Page 1: Policy Resolution Highlights
    p1 = doc.new_page()
    text_p1 = (
        "RESERVE BANK OF INDIA\n"
        "Monetary Policy Committee (MPC) Resolution\n"
        "Date: August 8, 2024\n\n"
        "Statement on Developmental and Regulatory Policies\n\n"
        "On the basis of an assessment of the current and evolving macroeconomic situation, "
        "the Monetary Policy Committee (MPC) at its meeting today decided to:\n"
        "- Keep the policy repo rate unchanged at 6.50 per cent.\n"
        "- Consequently, the standing deposit facility (SDF) rate remains at 6.25 per cent.\n"
        "- The marginal standing facility (MSF) rate and the Bank Rate at 6.75 per cent.\n\n"
        "The MPC also decided to remain focused on withdrawal of accommodation to ensure that inflation "
        "progressively aligns to the target, while supporting growth.\n"
    )
    p1.insert_text((50, 72), text_p1, fontsize=11)

    # Page 2: Macroeconomic Outlook
    p2 = doc.new_page()
    text_p2 = (
        "RESERVE BANK OF INDIA\n"
        "Macroeconomic Projections & Assessment - FY 2024-25\n\n"
        "1. Real GDP Growth:\n"
        "Real GDP growth for FY2024-25 is projected at 7.2 per cent, with Q1 at 7.1 per cent; "
        "Q2 at 7.2 per cent; Q3 at 7.3 per cent; and Q4 at 7.2 per cent. "
        "The risks are evenly balanced.\n\n"
        "2. Headline CPI Inflation:\n"
        "CPI inflation for 2024-25 is projected at 4.5 per cent, with Q1 at 4.9 per cent; "
        "Q2 at 4.4 per cent; Q3 at 4.7 per cent; and Q4 at 4.3 per cent.\n\n"
        "Governor, Reserve Bank of India: Shaktikanta Das.\n"
    )
    p2.insert_text((50, 72), text_p2, fontsize=11)

    doc.save(str(OUTPUT_PDF))
    doc.close()
    print(f"Unseen test PDF generated at: {OUTPUT_PDF}")

if __name__ == "__main__":
    generate_unseen_pdf()
