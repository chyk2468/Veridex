"""
Table Parser using pdfplumber.
Extracts tabular grids with explicit column-header and row-label bindings
to prevent cell-period misattribution in financial statements.
"""

import pdfplumber
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from models.evidence import Evidence

class TableCellRecord:
    def __init__(self, page_number: int, table_index: int, row_label: str, col_header: str, value: str, bbox: Optional[List[float]] = None):
        self.page_number = page_number
        self.table_index = table_index
        self.row_label = row_label
        self.col_header = col_header
        self.value = value
        self.bbox = bbox

    def to_context_string(self) -> str:
        return f"{self.row_label} | {self.col_header}: {self.value}"

class TableParser:
    """Extracts tables while strictly binding cells to column headers and row labels."""

    def __init__(self):
        pass

    def extract_tables_from_pdf(self, file_path: str, doc_id: str, max_pages: Optional[int] = None) -> Tuple[List[TableCellRecord], List[Evidence]]:
        """
        Extract tables across pages, generating bound cell records and table evidence.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        cell_records: List[TableCellRecord] = []
        table_evidence: List[Evidence] = []

        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            limit = min(total_pages, max_pages) if max_pages else total_pages

            for page_idx in range(limit):
                page = pdf.pages[page_idx]
                page_num = page_idx + 1
                tables = page.extract_tables()

                for t_idx, table in enumerate(tables):
                    if not table or len(table) < 2:
                        continue

                    # First row usually contains column headers
                    raw_headers = table[0]
                    headers = [str(h).strip().replace("\n", " ") if h else f"Col_{i}" for i, h in enumerate(raw_headers)]

                    # Full table string representation for evidence
                    table_rows_str = []
                    for row in table:
                        row_clean = [str(c).strip().replace("\n", " ") if c is not None else "" for c in row]
                        table_rows_str.append(" | ".join(row_clean))
                    full_table_text = "\n".join(table_rows_str)

                    ev_id = f"ev_{doc_id}_p{page_num}_tbl{t_idx}"
                    table_evidence.append(Evidence(
                        evidence_id=ev_id,
                        document_id=doc_id,
                        page_number=page_num,
                        section=f"Table {t_idx+1}",
                        text=full_table_text,
                        evidence_type="table",
                        extraction_method="pdfplumber",
                        confidence=0.95,
                        document_name=path.name
                    ))

                    # Process table rows
                    for r_idx, row in enumerate(table[1:], start=1):
                        if not row or not any(row):
                            continue
                        row_label = str(row[0]).strip().replace("\n", " ") if row[0] else f"Row_{r_idx}"

                        for c_idx, cell_value in enumerate(row[1:], start=1):
                            if cell_value is None or not str(cell_value).strip():
                                continue
                            val_str = str(cell_value).strip().replace("\n", " ")
                            col_header = headers[c_idx] if c_idx < len(headers) else f"Col_{c_idx}"

                            record = TableCellRecord(
                                page_number=page_num,
                                table_index=t_idx,
                                row_label=row_label,
                                col_header=col_header,
                                value=val_str
                            )
                            cell_records.append(record)

        return cell_records, table_evidence
