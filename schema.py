"""
Canonical schema definition for invoice extraction.
This is the contract between the extraction pipeline and the business.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Evidence(BaseModel):
    """Evidence for an extracted field."""
    page_number: int
    bbox: Optional[Dict[str, float]] = None  # {"x1": 0.0, "y1": 0.0, "x2": 100.0, "y2": 20.0}
    text_anchor: Optional[str] = None  # Surrounding text context


class FieldAudit(BaseModel):
    """Audit information for a single extracted field."""
    value: Any
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score from vendor")
    evidence: Optional[Evidence] = None
    pipeline_version: str
    vendor_version: str
    vendor_field_name: Optional[str] = None  # Original field name from vendor


class LineItem(BaseModel):
    """Line item from invoice."""
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: float
    audit: FieldAudit


class InvoiceSchema(BaseModel):
    """Canonical invoice schema with full audit trail."""
    # Core fields
    invoice_number: Optional[FieldAudit] = None
    invoice_date: Optional[FieldAudit] = None
    supplier_name: Optional[FieldAudit] = None
    supplier_id: Optional[FieldAudit] = None
    currency: Optional[FieldAudit] = None
    subtotal: Optional[FieldAudit] = None
    tax: Optional[FieldAudit] = None
    total: Optional[FieldAudit] = None
    po_number: Optional[FieldAudit] = None
    line_items: Optional[List[LineItem]] = None
    
    # Metadata
    doc_id: str
    extraction_timestamp: datetime
    vendor_name: str
    raw_vendor_output: Dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Result of validation checks."""
    passed: bool
    checks: Dict[str, bool] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class RoutingDecision(BaseModel):
    """Routing decision with reason codes."""
    outcome: str  # "AUTO_POST" or "NEEDS_REVIEW"
    reason_codes: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)

