"""
Business Intelligence Analyzer for Invoice Documents
Extracts business insights from Azure Document Intelligence results
"""
from typing import Dict, Any
from datetime import datetime


class BusinessAnalyzer:
    """Analyzes invoices for business intelligence and categorization."""
    
    def __init__(self):
        self.azure_cost_per_page = 0.01  # $0.01 per page
        
    def analyze_invoice(self, invoice_data: Dict[str, Any], azure_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract business insights from invoice.
        
        Args:
            invoice_data: Normalized invoice data
            azure_result: Raw Azure response
            
        Returns:
            Dictionary with business insights
        """
        # Get basic fields
        total = invoice_data.get("total") or 0
        supplier = invoice_data.get("supplier_name") or "Unknown"
        invoice_number = invoice_data.get("invoice_number") or "N/A"
        
        # Analyze and categorize
        category = self._categorize_document(supplier, invoice_data)
        priority = self._calculate_priority(total, invoice_data)
        cost = self._calculate_processing_cost(azure_result)
        urgency = self._determine_urgency(invoice_data)
        risk_level = self._assess_risk(invoice_data, total)
        
        return {
            "category": category,
            "priority": priority,
            "urgency": urgency,
            "processing_cost": cost,
            "total_amount": total,
            "supplier": supplier,
            "invoice_number": invoice_number,
            "risk_level": risk_level,
            "payment_terms": self._extract_payment_terms(invoice_data),
            "document_quality": self._assess_quality(invoice_data)
        }
    
    def _categorize_document(self, supplier: str, invoice_data: Dict[str, Any]) -> str:
        """
        Categorize document by type/service.
        Uses supplier name and invoice content to determine category.
        """
        supplier_lower = str(supplier).lower()
        invoice_num = str(invoice_data.get("invoice_number", "")).lower()
        
        # Service-based categories
        if any(word in supplier_lower for word in ["advertising", "marketing", "media"]):
            return "Marketing & Advertising"
        elif any(word in supplier_lower for word in ["finance", "bank", "capital", "consulting"]):
            return "Financial Services"
        elif any(word in supplier_lower for word in ["material", "supply", "parts", "equipment"]):
            return "Raw Materials & Supplies"
        elif any(word in supplier_lower for word in ["software", "saas", "tech", "cloud"]):
            return "Technology & Software"
        elif any(word in supplier_lower for word in ["utility", "electric", "water", "gas"]):
            return "Utilities"
        elif any(word in supplier_lower for word in ["legal", "attorney", "law"]):
            return "Legal Services"
        else:
            return "General Services"
    
    def _calculate_priority(self, total: float, invoice_data: Dict[str, Any]) -> str:
        """
        Calculate priority based on amount and other factors.
        
        Priority levels:
        - CRITICAL: >$50,000 or urgent keywords
        - HIGH: >$10,000
        - MEDIUM: >$1,000
        - LOW: <$1,000
        """
        if not total:
            return "MEDIUM"
        
        # Check for urgent keywords (if we had more text analysis)
        # For now, base on amount
        if total > 50000:
            return "CRITICAL"
        elif total > 10000:
            return "HIGH"
        elif total > 1000:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_processing_cost(self, azure_result: Dict[str, Any]) -> float:
        """
        Calculate cost of processing this document.
        Based on pages and Azure pricing.
        """
        # For simplicity, assume 1 page per invoice
        # In production, you'd get actual page count from Azure
        pages = 1
        return pages * self.azure_cost_per_page
    
    def _determine_urgency(self, invoice_data: Dict[str, Any]) -> str:
        """
        Determine payment urgency based on date and amount.
        
        Returns: "URGENT", "NORMAL", "LOW"
        """
        invoice_date = invoice_data.get("invoice_date")
        total = invoice_data.get("total") or 0
        
        # In production, calculate days until due date
        # For now, use simple heuristics
        
        if total > 100000:
            return "URGENT"
        elif total > 50000:
            return "NORMAL"
        else:
            return "LOW"
    
    def _assess_risk(self, invoice_data: Dict[str, Any], total: float) -> str:
        """
        Assess risk level based on various factors.
        
        Returns: "HIGH", "MEDIUM", "LOW"
        """
        validation_passed = invoice_data.get("validation_passed", False)
        confidence = invoice_data.get("confidence_scores", {}).get("total", 1.0)
        
        # High risk factors
        if not validation_passed:
            return "HIGH"
        elif confidence < 0.7:
            return "HIGH"
        elif total > 100000:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _extract_payment_terms(self, invoice_data: Dict[str, Any]) -> str:
        """Extract payment terms (simplified)."""
        # In production, extract from invoice text
        # For now, use defaults
        return "Net 30"
    
    def _assess_quality(self, invoice_data: Dict[str, Any]) -> str:
        """
        Assess document quality based on confidence scores.
        
        Returns: "EXCELLENT", "GOOD", "FAIR", "POOR"
        """
        conf_scores = invoice_data.get("confidence_scores", {})
        if not conf_scores:
            return "UNKNOWN"
        
        avg_confidence = sum(conf_scores.values()) / len(conf_scores)
        
        if avg_confidence >= 0.95:
            return "EXCELLENT"
        elif avg_confidence >= 0.85:
            return "GOOD"
        elif avg_confidence >= 0.70:
            return "FAIR"
        else:
            return "POOR"

