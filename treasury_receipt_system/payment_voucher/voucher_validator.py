"""Validation logic for Payment Vouchers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from ..account_parser import AccountDescriptions
from .voucher_classifier import VoucherClassification

LOGGER = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of voucher validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    compliance_checks: List[str]
    recommendations: List[str]


class VoucherValidator:
    """Validates Payment Vouchers against business rules and compliance requirements."""
    
    def __init__(self):
        self.business_rules = self._build_business_rules()
        self.compliance_rules = self._build_compliance_rules()
        self.validation_thresholds = self._build_validation_thresholds()
    
    def _build_business_rules(self) -> Dict[str, Dict]:
        """Build business rules for different voucher categories."""
        return {
            "Operating": {
                "max_amount": 50000,
                "requires_budget_check": True,
                "requires_receipt": True,
                "requires_justification": False,
                "allowed_gl_accounts": ["6*"],  # Expense accounts
                "prohibited_gl_accounts": ["1*", "2*", "3*"]  # Asset, Liability, Equity
            },
            "Capital": {
                "max_amount": 1000000,
                "requires_budget_check": True,
                "requires_receipt": True,
                "requires_justification": True,
                "requires_asset_approval": True,
                "allowed_gl_accounts": ["1*"],  # Asset accounts
                "prohibited_gl_accounts": ["6*"]  # Expense accounts
            },
            "Vendor": {
                "max_amount": 200000,
                "requires_budget_check": True,
                "requires_receipt": True,
                "requires_justification": True,
                "requires_vendor_verification": True,
                "requires_contract_check": True,
                "allowed_gl_accounts": ["6*", "2*"],  # Expense, Liability
                "prohibited_gl_accounts": ["1*", "3*"]  # Asset, Equity
            },
            "Personnel": {
                "max_amount": 500000,
                "requires_budget_check": True,
                "requires_receipt": False,
                "requires_justification": True,
                "requires_hr_approval": True,
                "requires_payroll_validation": True,
                "allowed_gl_accounts": ["6*"],  # Expense accounts
                "prohibited_gl_accounts": ["1*", "2*", "3*"]  # Asset, Liability, Equity
            },
            "Administrative": {
                "max_amount": 25000,
                "requires_budget_check": True,
                "requires_receipt": True,
                "requires_justification": False,
                "allowed_gl_accounts": ["6*"],  # Expense accounts
                "prohibited_gl_accounts": ["1*", "2*", "3*"]  # Asset, Liability, Equity
            }
        }
    
    def _build_compliance_rules(self) -> Dict[str, List[str]]:
        """Build compliance rules for different scenarios."""
        return {
            "high_amount": [
                "executive_approval_required",
                "additional_documentation",
                "post_payment_audit"
            ],
            "vendor_payment": [
                "vendor_verification",
                "contract_validation",
                "tax_compliance_check"
            ],
            "capital_expenditure": [
                "asset_approval",
                "depreciation_setup",
                "budget_allocation"
            ],
            "personnel_cost": [
                "hr_approval",
                "payroll_validation",
                "benefit_verification"
            ],
            "international_payment": [
                "foreign_exchange_approval",
                "regulatory_compliance",
                "tax_withholding"
            ]
        }
    
    def _build_validation_thresholds(self) -> Dict[str, float]:
        """Build validation thresholds for different checks."""
        return {
            "high_amount_threshold": 100000,
            "executive_approval_threshold": 500000,
            "budget_check_threshold": 10000,
            "vendor_verification_threshold": 5000
        }
    
    def validate_voucher(self, 
                        account_desc: AccountDescriptions,
                        amount: float,
                        classification: VoucherClassification,
                        additional_data: Optional[Dict] = None) -> ValidationResult:
        """Validate a Payment Voucher against all rules."""
        
        errors = []
        warnings = []
        compliance_checks = []
        recommendations = []
        
        # Basic validation
        basic_errors, basic_warnings = self._validate_basic(amount, classification)
        errors.extend(basic_errors)
        warnings.extend(basic_warnings)
        
        # Business rules validation
        business_errors, business_warnings = self._validate_business_rules(
            account_desc, amount, classification
        )
        errors.extend(business_errors)
        warnings.extend(business_warnings)
        
        # Compliance validation
        compliance_errors, compliance_warnings, compliance_checks = self._validate_compliance(
            account_desc, amount, classification, additional_data
        )
        errors.extend(compliance_errors)
        warnings.extend(compliance_warnings)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            account_desc, amount, classification, errors, warnings
        )
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            compliance_checks=compliance_checks,
            recommendations=recommendations
        )
    
    def _validate_basic(self, amount: float, classification: VoucherClassification) -> Tuple[List[str], List[str]]:
        """Validate basic voucher requirements."""
        errors = []
        warnings = []
        
        # Amount validation
        if amount <= 0:
            errors.append("Amount must be greater than zero")
        elif amount > 10000000:  # $10M threshold
            errors.append("Amount exceeds maximum allowed limit")
        elif amount >= 1000000:  # $1M threshold
            warnings.append("High amount - additional approval may be required")
        
        # Classification validation
        if classification.category == "Unknown":
            errors.append("Transaction category could not be determined")
        
        if classification.risk_level == "High" and amount >= 50000:
            warnings.append("High-risk transaction with significant amount")
        
        return errors, warnings
    
    def _validate_business_rules(self, 
                                account_desc: AccountDescriptions,
                                amount: float, 
                                classification: VoucherClassification) -> Tuple[List[str], List[str]]:
        """Validate against business rules."""
        errors = []
        warnings = []
        
        category = classification.category
        if category not in self.business_rules:
            errors.append(f"Unknown category: {category}")
            return errors, warnings
        
        rules = self.business_rules[category]
        
        # Amount validation
        if amount > rules["max_amount"]:
            errors.append(f"Amount ${amount:,.2f} exceeds maximum for {category} category (${rules['max_amount']:,.2f})")
        
        # GL Account validation
        gl_account = account_desc.gl_account
        if rules["allowed_gl_accounts"]:
            if not any(gl_account.startswith(pattern.replace("*", "")) for pattern in rules["allowed_gl_accounts"]):
                errors.append(f"GL Account {gl_account} not allowed for {category} category")
        
        if rules["prohibited_gl_accounts"]:
            if any(gl_account.startswith(pattern.replace("*", "")) for pattern in rules["prohibited_gl_accounts"]):
                errors.append(f"GL Account {gl_account} prohibited for {category} category")
        
        # Budget check requirement
        if rules["requires_budget_check"] and amount >= self.validation_thresholds["budget_check_threshold"]:
            warnings.append("Budget availability check required")
        
        # Receipt requirement
        if rules["requires_receipt"]:
            warnings.append("Receipt documentation required")
        
        # Justification requirement
        if rules["requires_justification"]:
            warnings.append("Business justification required")
        
        return errors, warnings
    
    def _validate_compliance(self, 
                           account_desc: AccountDescriptions,
                           amount: float,
                           classification: VoucherClassification,
                           additional_data: Optional[Dict] = None) -> Tuple[List[str], List[str], List[str]]:
        """Validate compliance requirements."""
        errors = []
        warnings = []
        compliance_checks = []
        
        # High amount compliance
        if amount >= self.validation_thresholds["high_amount_threshold"]:
            compliance_checks.extend(self.compliance_rules["high_amount"])
            warnings.append("High amount - additional compliance checks required")
        
        # Category-specific compliance
        if classification.category == "Vendor":
            compliance_checks.extend(self.compliance_rules["vendor_payment"])
            warnings.append("Vendor payment - compliance checks required")
        
        if classification.category == "Capital":
            compliance_checks.extend(self.compliance_rules["capital_expenditure"])
            warnings.append("Capital expenditure - compliance checks required")
        
        if classification.category == "Personnel":
            compliance_checks.extend(self.compliance_rules["personnel_cost"])
            warnings.append("Personnel cost - compliance checks required")
        
        # International payment check (if additional data provided)
        if additional_data and additional_data.get("is_international", False):
            compliance_checks.extend(self.compliance_rules["international_payment"])
            warnings.append("International payment - additional compliance required")
        
        # Duplicate payment check
        if additional_data and additional_data.get("vendor_id"):
            warnings.append("Verify no duplicate payments to same vendor")
        
        return errors, warnings, compliance_checks
    
    def _generate_recommendations(self, 
                                 account_desc: AccountDescriptions,
                                 amount: float,
                                 classification: VoucherClassification,
                                 errors: List[str],
                                 warnings: List[str]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Amount-based recommendations
        if amount >= 100000:
            recommendations.append("Consider breaking into smaller payments for better control")
        
        if amount >= 500000:
            recommendations.append("Executive approval recommended for amounts over $500K")
        
        # Category-based recommendations
        if classification.category == "Capital":
            recommendations.append("Ensure asset tracking and depreciation setup")
        
        if classification.category == "Vendor":
            recommendations.append("Verify vendor credentials and contract terms")
        
        if classification.category == "Personnel":
            recommendations.append("Coordinate with HR for payroll integration")
        
        # Risk-based recommendations
        if classification.risk_level == "High":
            recommendations.append("Enhanced documentation and approval process recommended")
        
        # Error-based recommendations
        if any("GL Account" in error for error in errors):
            recommendations.append("Review GL account mapping with Finance team")
        
        if any("budget" in warning.lower() for warning in warnings):
            recommendations.append("Verify budget availability before processing")
        
        return recommendations
    
    def validate_batch(self, vouchers: List[Dict]) -> Dict[str, ValidationResult]:
        """Validate a batch of vouchers."""
        results = {}
        
        for voucher in vouchers:
            voucher_id = voucher.get("voucher_number", f"voucher_{len(results)}")
            result = self.validate_voucher(
                voucher.get("account_desc"),
                voucher.get("amount", 0),
                voucher.get("classification"),
                voucher.get("additional_data")
            )
            results[voucher_id] = result
        
        return results
    
    def get_validation_summary(self, results: Dict[str, ValidationResult]) -> Dict:
        """Get summary of validation results."""
        total_vouchers = len(results)
        valid_vouchers = sum(1 for r in results.values() if r.is_valid)
        invalid_vouchers = total_vouchers - valid_vouchers
        
        total_errors = sum(len(r.errors) for r in results.values())
        total_warnings = sum(len(r.warnings) for r in results.values())
        
        return {
            "total_vouchers": total_vouchers,
            "valid_vouchers": valid_vouchers,
            "invalid_vouchers": invalid_vouchers,
            "validation_rate": f"{(valid_vouchers/total_vouchers)*100:.1f}%" if total_vouchers > 0 else "0%",
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "average_errors_per_voucher": total_errors / total_vouchers if total_vouchers > 0 else 0,
            "average_warnings_per_voucher": total_warnings / total_vouchers if total_vouchers > 0 else 0
        }
