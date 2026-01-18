"""
Validation and routing logic - the finance-grade layer.
"""
from typing import Dict, List, Optional
from datetime import datetime
from schema import InvoiceSchema, ValidationResult, RoutingDecision


class Validator:
    """Validates invoices and makes routing decisions."""
    
    def __init__(
        self,
        currency_tolerance: Dict[str, float] = None,
        high_total_threshold: float = 100000.0,
        low_confidence_threshold: float = 0.7,
        required_fields: List[str] = None
    ):
        """
        Initialize validator with configurable thresholds.
        
        Args:
            currency_tolerance: Tolerance per currency for reconciliation (default: 0.01 for all)
            high_total_threshold: Threshold for manual review (default: 100000)
            low_confidence_threshold: Minimum confidence for auto-post (default: 0.7)
            required_fields: Fields that must be present (default: invoice_number, invoice_date, supplier_name, total)
        """
        self.currency_tolerance = currency_tolerance or {"USD": 0.01, "EUR": 0.01, "GBP": 0.01}
        self.high_total_threshold = high_total_threshold
        self.low_confidence_threshold = low_confidence_threshold
        self.required_fields = required_fields or [
            "invoice_number", "invoice_date", "supplier_name", "total"
        ]
    
    def validate(self, invoice: InvoiceSchema) -> ValidationResult:
        """
        Run all validation checks.
        
        Returns:
            ValidationResult with passed flag and detailed checks
        """
        checks = {}
        errors = []
        warnings = []
        
        # Schema constraints
        checks["required_fields_present"] = self._check_required_fields(invoice, errors)
        checks["date_format_valid"] = self._check_date_format(invoice, errors)
        checks["currency_valid"] = self._check_currency(invoice, errors)
        
        # Reconciliation
        checks["reconciliation_pass"] = self._check_reconciliation(invoice, errors)
        
        # Policy rules
        checks["total_within_threshold"] = self._check_total_threshold(invoice, warnings)
        checks["po_present"] = self._check_po_present(invoice, warnings)
        
        passed = len(errors) == 0
        
        return ValidationResult(
            passed=passed,
            checks=checks,
            errors=errors,
            warnings=warnings
        )
    
    def _check_required_fields(self, invoice: InvoiceSchema, errors: List[str]) -> bool:
        """Check if all required fields are present."""
        missing = []
        for field in self.required_fields:
            field_audit = getattr(invoice, field, None)
            if field_audit is None or field_audit.value is None:
                missing.append(field)
        
        if missing:
            errors.append(f"Missing required fields: {', '.join(missing)}")
            return False
        return True
    
    def _check_date_format(self, invoice: InvoiceSchema, errors: List[str]) -> bool:
        """Check if invoice_date is valid."""
        if invoice.invoice_date is None or invoice.invoice_date.value is None:
            return True  # Already caught by required fields check
        
        date_value = invoice.invoice_date.value
        if isinstance(date_value, str):
            try:
                datetime.fromisoformat(date_value.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                try:
                    datetime.strptime(date_value, "%Y-%m-%d")
                except ValueError:
                    errors.append(f"Invalid date format: {date_value}")
                    return False
        elif isinstance(date_value, datetime):
            pass  # Valid datetime object
        else:
            errors.append(f"Date must be string or datetime, got {type(date_value)}")
            return False
        
        return True
    
    def _check_currency(self, invoice: InvoiceSchema, errors: List[str]) -> bool:
        """Check if currency code is recognized."""
        valid_currencies = {"USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CNY", "INR"}
        
        if invoice.currency is None or invoice.currency.value is None:
            return True  # Optional field
        
        currency = str(invoice.currency.value).upper()
        if currency not in valid_currencies:
            errors.append(f"Unrecognized currency: {currency}")
            return False
        
        return True
    
    def _check_reconciliation(self, invoice: InvoiceSchema, errors: List[str]) -> bool:
        """Check if subtotal + tax = total (within tolerance)."""
        if invoice.subtotal is None or invoice.tax is None or invoice.total is None:
            return True  # Missing fields already caught
        
        subtotal = float(invoice.subtotal.value) if invoice.subtotal.value else 0.0
        tax = float(invoice.tax.value) if invoice.tax.value else 0.0
        total = float(invoice.total.value) if invoice.total.value else 0.0
        
        currency = "USD"  # Default
        if invoice.currency and invoice.currency.value:
            currency = str(invoice.currency.value).upper()
        
        tolerance = self.currency_tolerance.get(currency, 0.01)
        calculated_total = subtotal + tax
        difference = abs(calculated_total - total)
        
        if difference > tolerance:
            errors.append(
                f"Reconciliation failed: subtotal ({subtotal}) + tax ({tax}) = {calculated_total}, "
                f"but total = {total} (difference: {difference:.2f}, tolerance: {tolerance})"
            )
            return False
        
        return True
    
    def _check_total_threshold(self, invoice: InvoiceSchema, warnings: List[str]) -> bool:
        """Check if total exceeds threshold for manual review."""
        if invoice.total is None or invoice.total.value is None:
            return True
        
        total = float(invoice.total.value)
        if total > self.high_total_threshold:
            warnings.append(f"High total amount: {total} (threshold: {self.high_total_threshold})")
            return False
        return True
    
    def _check_po_present(self, invoice: InvoiceSchema, warnings: List[str]) -> bool:
        """Check if PO number is present."""
        if invoice.po_number is None or invoice.po_number.value is None:
            warnings.append("PO number missing")
            return False
        return True
    
    def route(self, invoice: InvoiceSchema, validation: ValidationResult) -> RoutingDecision:
        """
        Make routing decision based on validation results.
        
        Returns:
            RoutingDecision with outcome and reason codes
        """
        reason_codes = []
        
        # Check validation errors
        if not validation.passed:
            reason_codes.append("VALIDATION_FAILED")
            if "reconciliation_pass" in validation.checks and not validation.checks["reconciliation_pass"]:
                reason_codes.append("TOTAL_MISMATCH")
            if "required_fields_present" in validation.checks and not validation.checks["required_fields_present"]:
                reason_codes.append("MISSING_REQUIRED_FIELDS")
        
        # Check confidence scores
        critical_fields = ["invoice_number", "total", "invoice_date"]
        low_confidence_fields = []
        for field in critical_fields:
            field_audit = getattr(invoice, field, None)
            if field_audit and field_audit.confidence < self.low_confidence_threshold:
                low_confidence_fields.append(field)
        
        if low_confidence_fields:
            reason_codes.append("LOW_CONFIDENCE")
            reason_codes.append(f"LOW_CONF_{'_'.join(low_confidence_fields).upper()}")
        
        # Check warnings
        if "total_within_threshold" in validation.checks and not validation.checks["total_within_threshold"]:
            reason_codes.append("HIGH_TOTAL")
        
        if "po_present" in validation.checks and not validation.checks["po_present"]:
            reason_codes.append("MISSING_PO")
        
        # Calculate overall confidence (average of critical fields)
        confidence_scores = []
        for field in critical_fields:
            field_audit = getattr(invoice, field, None)
            if field_audit:
                confidence_scores.append(field_audit.confidence)
        
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Decision logic
        if len(reason_codes) == 0 and overall_confidence >= self.low_confidence_threshold:
            outcome = "AUTO_POST"
        else:
            outcome = "NEEDS_REVIEW"
        
        return RoutingDecision(
            outcome=outcome,
            reason_codes=reason_codes,
            confidence_score=overall_confidence
        )

