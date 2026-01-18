"""
Normalization layer: converts vendor-specific output to canonical schema.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from schema import InvoiceSchema, FieldAudit, Evidence, LineItem


class Normalizer:
    """Normalizes vendor output to canonical schema."""
    
    def __init__(self, pipeline_version: str = "1.0.0"):
        self.pipeline_version = pipeline_version
    
    def normalize(self, vendor_output: Dict[str, Any], vendor_name: str, vendor_version: str) -> InvoiceSchema:
        """
        Normalize vendor output to canonical schema.
        
        Args:
            vendor_output: Raw output from vendor extractor
            vendor_name: Name of the vendor
            vendor_version: Version of the vendor extractor
            
        Returns:
            Normalized InvoiceSchema
        """
        doc_id = vendor_output.get("document_id") or vendor_output.get("id", "unknown")
        
        if vendor_name == "vendor_a":
            return self._normalize_vendor_a(vendor_output, doc_id, vendor_name, vendor_version)
        elif vendor_name == "vendor_b":
            return self._normalize_vendor_b(vendor_output, doc_id, vendor_name, vendor_version)
        else:
            # Default to vendor_a format
            return self._normalize_vendor_a(vendor_output, doc_id, vendor_name, vendor_version)
    
    def _normalize_vendor_a(self, output: Dict[str, Any], doc_id: str, vendor_name: str, vendor_version: str) -> InvoiceSchema:
        """Normalize vendor A format."""
        fields = output.get("fields", {})
        
        def create_field_audit(field_name: str, vendor_field_name: Optional[str] = None) -> Optional[FieldAudit]:
            if field_name not in fields:
                return None
            
            field_data = fields[field_name]
            value = field_data.get("value")
            confidence = field_data.get("confidence", 0.0)
            
            return FieldAudit(
                value=value,
                confidence=confidence,
                evidence=Evidence(page_number=1),  # Simplified for demo
                pipeline_version=self.pipeline_version,
                vendor_version=vendor_version,
                vendor_field_name=vendor_field_name or field_name
            )
        
        # Normalize line items
        line_items = None
        if "line_items" in output:
            line_items = []
            for item in output["line_items"]:
                line_items.append(LineItem(
                    description=item.get("description", ""),
                    quantity=item.get("quantity"),
                    unit_price=item.get("unit_price"),
                    amount=item.get("amount", 0.0),
                    audit=FieldAudit(
                        value=item,
                        confidence=item.get("confidence", 0.0),
                        evidence=Evidence(page_number=1),
                        pipeline_version=self.pipeline_version,
                        vendor_version=vendor_version,
                        vendor_field_name="line_item"
                    )
                ))
        
        return InvoiceSchema(
            doc_id=doc_id,
            extraction_timestamp=datetime.now(),
            vendor_name=vendor_name,
            raw_vendor_output=output,
            invoice_number=create_field_audit("invoice_number"),
            invoice_date=create_field_audit("invoice_date"),
            supplier_name=create_field_audit("supplier_name"),
            supplier_id=create_field_audit("supplier_id"),
            currency=create_field_audit("currency"),
            subtotal=create_field_audit("subtotal"),
            tax=create_field_audit("tax"),
            total=create_field_audit("total"),
            po_number=create_field_audit("po_number"),
            line_items=line_items
        )
    
    def _normalize_vendor_b(self, output: Dict[str, Any], doc_id: str, vendor_name: str, vendor_version: str) -> InvoiceSchema:
        """Normalize vendor B format."""
        financial = output.get("extracted_data", {}).get("financial", {})
        
        def create_field_audit(vendor_field: str, canonical_field: str) -> Optional[FieldAudit]:
            if vendor_field not in financial:
                return None
            
            field_data = financial[vendor_field]
            value = field_data.get("text")
            confidence = field_data.get("score", 0.0)
            
            # Convert string values to appropriate types
            if canonical_field in ["subtotal", "tax", "total"]:
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    return None
            
            return FieldAudit(
                value=value,
                confidence=confidence,
                evidence=Evidence(page_number=1),
                pipeline_version=self.pipeline_version,
                vendor_version=vendor_version,
                vendor_field_name=vendor_field
            )
        
        # Map vendor B fields to canonical
        field_mapping = {
            "invoice_num": "invoice_number",
            "date": "invoice_date",
            "vendor_name": "supplier_name",
            "vendor_id": "supplier_id",
            "currency_code": "currency",
            "amount_before_tax": "subtotal",
            "tax_amount": "tax",
            "amount_due": "total",
            "purchase_order": "po_number"
        }
        
        normalized_fields = {}
        for vendor_field, canonical_field in field_mapping.items():
            audit = create_field_audit(vendor_field, canonical_field)
            if audit:
                normalized_fields[canonical_field] = audit
        
        # Normalize line items
        line_items = None
        items = output.get("extracted_data", {}).get("items", [])
        if items:
            line_items = []
            for item in items:
                line_items.append(LineItem(
                    description=item.get("desc", ""),
                    quantity=item.get("qty"),
                    unit_price=item.get("price"),
                    amount=item.get("line_total", 0.0),
                    audit=FieldAudit(
                        value=item,
                        confidence=item.get("score", 0.0),
                        evidence=Evidence(page_number=1),
                        pipeline_version=self.pipeline_version,
                        vendor_version=vendor_version,
                        vendor_field_name="line_item"
                    )
                ))
        
        return InvoiceSchema(
            doc_id=doc_id,
            extraction_timestamp=datetime.now(),
            vendor_name=vendor_name,
            raw_vendor_output=output,
            invoice_number=normalized_fields.get("invoice_number"),
            invoice_date=normalized_fields.get("invoice_date"),
            supplier_name=normalized_fields.get("supplier_name"),
            supplier_id=normalized_fields.get("supplier_id"),
            currency=normalized_fields.get("currency"),
            subtotal=normalized_fields.get("subtotal"),
            tax=normalized_fields.get("tax"),
            total=normalized_fields.get("total"),
            po_number=normalized_fields.get("po_number"),
            line_items=line_items
        )

