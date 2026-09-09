"""
Evidence model.
Evidence is a first-class citizen linking extracted facts to exact PDF sources.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class Evidence(BaseModel):
    evidence_id: str
    document_id: str
    page_id: Optional[str] = None
    page_number: int  # 1-indexed
    section: Optional[str] = None
    text: str
    bbox: Optional[List[float]] = None  # [x0, y0, x1, y1] coordinates
    evidence_type: str = "text"  # text, table, footnote, caption
    extraction_method: str = "pymupdf"
    confidence: float = 1.0
    document_name: Optional[str] = None
