"""
Unit tests for PDF Parser and Table Parser.
"""

import pytest
from pathlib import Path
from core.parser import PDFParser
from core.table_parser import TableParser

SAMPLE_PDF = Path("../starter-datasets/delhivery/03-delhivery-q4-fy24-earnings-presentation.pdf")

def test_pdf_parser_page_tracking():
    parser = PDFParser()
    doc, evidence = parser.parse_document(str(SAMPLE_PDF))

    assert doc.page_count == 27
    assert len(doc.pages) == 27
    assert doc.pages[0].page_number == 1  # 1-indexed
    assert doc.pages[-1].page_number == 27
    assert len(doc.content_hash) == 64  # SHA-256

def test_evidence_coordinates_and_blocks():
    parser = PDFParser()
    doc, evidence = parser.parse_document(str(SAMPLE_PDF))

    assert len(evidence) > 100
    sample_ev = evidence[0]
    assert sample_ev.document_id == doc.document_id
    assert sample_ev.page_number >= 1
    assert len(sample_ev.bbox) == 4
    assert sample_ev.bbox[0] <= sample_ev.bbox[2]
    assert sample_ev.bbox[1] <= sample_ev.bbox[3]

def test_table_parser_header_binding():
    table_parser = TableParser()
    cells, tbl_ev = table_parser.extract_tables_from_pdf(str(SAMPLE_PDF), "test_doc", max_pages=10)

    assert len(tbl_ev) > 0
    assert len(cells) > 0
    sample_cell = cells[0]
    assert sample_cell.row_label is not None
    assert sample_cell.col_header is not None
    assert sample_cell.value is not None
    assert " | " in sample_cell.to_context_string()
