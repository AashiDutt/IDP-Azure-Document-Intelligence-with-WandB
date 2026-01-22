"""
Azure Document Intelligence Adapter
Converts Azure Form Recognizer responses to our canonical schema.
"""
import os
from typing import Dict, Any
from datetime import datetime
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest


class AzureDocumentIntelligenceAdapter:
    """
    Adapter for Azure Document Intelligence (Form Recognizer).
    """
    
    def __init__(self, endpoint: str, api_key: str, model_id: str = "prebuilt-invoice"):
        """
        Initialize Azure adapter.
        
        Args:
            endpoint: Azure endpoint URL
            api_key: Azure API key
            model_id: Model ID (default: prebuilt-invoice)
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.model_id = model_id
        self.client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
    
    def extract_invoice(self, file_path_or_url: str, doc_id: str) -> Dict[str, Any]:
        """
        Extract invoice data using Azure Document Intelligence.
        
        Args:
            file_path_or_url: Path to local file or URL
            doc_id: Document identifier
            
        Returns:
            Standardized extraction result
        """
        print(f"  - Sending to Azure Document Intelligence...")
        
        # Determine if input is URL or file path
        if file_path_or_url.startswith(('http://', 'https://')):
            # URL-based analysis
            poller = self.client.begin_analyze_document(
                self.model_id,
                AnalyzeDocumentRequest(url_source=file_path_or_url)
            )
        else:
            # File-based analysis
            if not os.path.exists(file_path_or_url):
                raise FileNotFoundError(f"File not found: {file_path_or_url}")
            
            with open(file_path_or_url, 'rb') as f:
                file_content = f.read()
            
            poller = self.client.begin_analyze_document(
                self.model_id,
                body=file_content,
                content_type="application/octet-stream"
            )
        
        # Wait for result
        result = poller.result()
        print(f"  * Extraction completed")
        
        # Convert to standard format
        return self._normalize_azure_response(result, doc_id)
    
    def _normalize_azure_response(self, azure_result: Any, doc_id: str) -> Dict[str, Any]:
        """Convert Azure response to standard format."""
        if not azure_result.documents:
            raise ValueError("No documents found in Azure response")
        
        # Take first document
        invoice = azure_result.documents[0]
        fields = invoice.fields
        
        def get_field(field_name: str) -> Dict[str, Any]:
            """Extract field with value and confidence."""
            field = fields.get(field_name)
            if not field:
                return {"value": None, "confidence": 0.0}
            
            # Extract value based on type
            value = None
            if hasattr(field, 'value_string'):
                value = field.value_string
            elif hasattr(field, 'value_number'):
                value = field.value_number
            elif hasattr(field, 'value_date'):
                value = str(field.value_date) if field.value_date else None
            elif hasattr(field, 'value_currency'):
                value = field.value_currency.amount if field.value_currency else None
            elif hasattr(field, 'value_address'):
                value = str(field.value_address) if field.value_address else None
            
            return {
                "value": value,
                "confidence": field.confidence if hasattr(field, 'confidence') else 0.0
            }
        
        # Extract line items first
        line_items_data = self._extract_line_items(fields.get("Items"))
        
        # Get total field
        total_field = get_field("InvoiceTotal")
        
        # If total is null/zero but we have line items, calculate from line items
        if (total_field["value"] is None or total_field["value"] == 0) and line_items_data:
            calculated_total = sum(item.get("amount", 0) for item in line_items_data if item.get("amount"))
            if calculated_total > 0:
                total_field = {
                    "value": calculated_total,
                    "confidence": total_field["confidence"]  # Keep original confidence
                }
                print(f"    INFO: Calculated total from line items: ${calculated_total:.2f}")
        
        # Map Azure fields to our canonical schema
        normalized = {
            "document_id": doc_id,
            "extraction_metadata": {
                "vendor": "azure_document_intelligence",
                "version": self.model_id,
                "timestamp": datetime.now().isoformat()
            },
            "fields": {
                "invoice_number": get_field("InvoiceId"),
                "invoice_date": get_field("InvoiceDate"),
                "supplier_name": get_field("VendorName"),
                "supplier_id": get_field("VendorTaxId"),
                "currency": {"value": "USD", "confidence": 1.0},  # Azure returns amounts in currency field
                "subtotal": get_field("SubTotal"),
                "tax": get_field("TotalTax"),
                "total": total_field,  # Use calculated or extracted total
                "po_number": get_field("PurchaseOrder")
            },
            "line_items": line_items_data
        }
        
        return normalized
    
    def _extract_line_items(self, items_field) -> list:
        """Extract line items from Azure response."""
        if not items_field or not hasattr(items_field, 'value_array'):
            return []
        
        line_items = []
        for item in items_field.value_array:
            if not hasattr(item, 'value_object'):
                continue
            
            item_obj = item.value_object
            
            # Extract item fields
            description = item_obj.get("Description")
            quantity = item_obj.get("Quantity")
            unit_price = item_obj.get("UnitPrice")
            amount = item_obj.get("Amount")
            
            line_item = {
                "description": description.value_string if description else "",
                "quantity": quantity.value_number if quantity else None,
                "unit_price": unit_price.value_currency.amount if (unit_price and hasattr(unit_price, 'value_currency')) else None,
                "amount": amount.value_currency.amount if (amount and hasattr(amount, 'value_currency')) else 0.0,
                "confidence": item.confidence if hasattr(item, 'confidence') else 0.0
            }
            
            line_items.append(line_item)
        
        return line_items

