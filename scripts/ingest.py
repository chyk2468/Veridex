"""
Document Ingestion CLI script.
Usage:
    python scripts/ingest.py path/to/document.pdf [--max-pages N]
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.pipeline import FactKnowledgePipeline

def main():
    parser = argparse.ArgumentParser(description="Ingest a PDF document into the Fact Knowledge Layer.")
    parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
    parser.add_argument("--max-pages", type=int, default=None, help="Maximum number of pages to process")
    args = parser.parse_args()

    pipeline = FactKnowledgePipeline()
    print(f"Ingesting: {args.pdf_path} (max_pages={args.max_pages})...")
    result = pipeline.ingest_document(args.pdf_path, max_pages=args.max_pages)
    print("\nIngestion Result:")
    for k, v in result.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
