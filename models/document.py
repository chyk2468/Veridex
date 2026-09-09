"""
Document and Page models.
Represents ingested PDF documents and individual page metadata.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import hashlib

class Page(BaseModel):
    page_id: str
    document_id: str
    page_number: int  # 1-indexed page number from PDF
    text: str
    extraction_method: str = "pymupdf"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Document(BaseModel):
    document_id: str
    filename: str
    title: Optional[str] = None
    page_count: int
    content_hash: str
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_status: str = "pending"  # pending, processing, completed, failed
    processing_duration: Optional[float] = None
    extraction_method: str = "hybrid_pymupdf_pdfplumber"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    pages: List[Page] = Field(default_factory=list)

    @staticmethod
    def compute_hash(file_bytes: bytes) -> str:
        """Compute SHA-256 hash of file content to prevent duplicates."""
        return hashlib.sha256(file_bytes).hexdigest()
