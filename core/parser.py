"""
Page-aware PDF Parser.
Extracts structured text blocks, headings, coordinates, and page metadata using PyMuPDF.
Preserves strict 1-indexed page references for evidence grounding.
"""

import os
import uuid
import hashlib
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import fitz  # PyMuPDF

from models.document import Document, Page
from models.evidence import Evidence

class PDFParser:
    """Extracts structured text blocks, metadata, and page hierarchy from PDFs."""

    def __init__(self):
        pass

    def parse_document(self, file_path: str, document_id: Optional[str] = None) -> Tuple[Document, List[Evidence]]:
        """
        Parse an entire PDF file, returning a Document model with Page objects
        and a collection of Evidence blocks with exact bounding coordinates and page numbers.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found at: {file_path}")

        file_bytes = path.read_bytes()
        content_hash = Document.compute_hash(file_bytes)
        doc_id = document_id or f"doc_{uuid.uuid4().hex[:10]}"

        doc = fitz.open(file_path)
        page_count = len(doc)
        title = doc.metadata.get("title") or path.stem

        pages: List[Page] = []
        evidence_list: List[Evidence] = []

        for page_idx in range(page_count):
            pdf_page = doc[page_idx]
            page_num = page_idx + 1  # 1-indexed page number
            page_id = f"{doc_id}_p{page_num}"
            
            # Extract plain text
            page_text = pdf_page.get_text()

            pages.append(Page(
                page_id=page_id,
                document_id=doc_id,
                page_number=page_num,
                text=page_text,
                extraction_method="pymupdf",
                metadata={"width": pdf_page.rect.width, "height": pdf_page.rect.height}
            ))

            # Extract detailed text blocks with coordinates
            # blocks: (x0, y0, x1, y1, text, block_no, block_type)
            blocks = pdf_page.get_text("blocks")
            for b_idx, b in enumerate(blocks):
                # block_type 0 is text
                if b[6] == 0:
                    text_content = b[4].strip()
                    if not text_content:
                        continue
                    
                    bbox = [round(b[0], 2), round(b[1], 2), round(b[2], 2), round(b[3], 2)]
                    evidence_id = f"ev_{doc_id}_p{page_num}_b{b_idx}"

                    evidence_list.append(Evidence(
                        evidence_id=evidence_id,
                        document_id=doc_id,
                        page_id=page_id,
                        page_number=page_num,
                        text=text_content,
                        bbox=bbox,
                        evidence_type="text",
                        extraction_method="pymupdf",
                        confidence=1.0,
                        document_name=path.name
                    ))

        doc.close()

        document = Document(
            document_id=doc_id,
            filename=path.name,
            title=title,
            page_count=page_count,
            content_hash=content_hash,
            processing_status="parsed",
            extraction_method="pymupdf",
            pages=pages
        )

        return document, evidence_list
