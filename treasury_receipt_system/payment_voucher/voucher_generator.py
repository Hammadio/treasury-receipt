"""Payment Voucher generator with advanced formatting and templates."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from ..account_parser import AccountDescriptions
from .voucher_classifier import VoucherClassification

LOGGER = logging.getLogger(__name__)


@dataclass
class VoucherMetadata:
    """Metadata for Payment Voucher generation."""
    voucher_number: str
    creation_date: str
    created_by: str
    department: str
    project_code: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_id: Optional[str] = None
    contract_reference: Optional[str] = None
    due_date: Optional[str] = None


class PaymentVoucherGenerator:
    """Advanced Payment Voucher generator with multiple templates."""
    
    def __init__(self, template_style: str = "standard"):
        self.template_style = template_style
        self.templates = self._build_templates()
    
    def _build_templates(self) -> Dict[str, Dict]:
        """Build different voucher templates."""
        return {
            "standard": {
                "header_format": "PAYMENT VOUCHER",
                "separator": "=" * 50,
                "include_approval_workflow": True,
                "include_compliance_checks": True,
                "include_vendor_info": True
            },
            "executive": {
                "header_format": "EXECUTIVE PAYMENT VOUCHER",
                "separator": "=" * 60,
                "include_approval_workflow": True,
                "include_compliance_checks": True,
                "include_vendor_info": True,
                "include_risk_assessment": True
            },
            "simple": {
                "header_format": "PAYMENT VOUCHER",
                "separator": "-" * 30,
                "include_approval_workflow": False,
                "include_compliance_checks": False,
                "include_vendor_info": False
            }
        }
    
    def generate_voucher(self, 
                        account_desc: AccountDescriptions,
                        amount: float,
                        classification: VoucherClassification,
                        metadata: VoucherMetadata,
                        template_style: Optional[str] = None) -> str:
        """Generate a Payment Voucher with specified template."""
        
        template = self.templates.get(template_style or self.template_style, self.templates["standard"])
        
        lines = []
        
        # Header
        lines.append(template["header_format"])
        lines.append(template["separator"])
        
        # Voucher Information
        lines.extend(self._generate_voucher_info(metadata))
        lines.append("")
        
        # Account Details
        lines.extend(self._generate_account_details(account_desc))
        lines.append("")
        
        # Payment Details
        lines.extend(self._generate_payment_details(amount, classification))
        lines.append("")
        
        # Classification Details
        lines.extend(self._generate_classification_details(classification))
        lines.append("")
        
        # Vendor Information (if applicable)
        if template["include_vendor_info"] and metadata.vendor_name:
            lines.extend(self._generate_vendor_info(metadata))
            lines.append("")
        
        # Compliance Checks
        if template["include_compliance_checks"]:
            lines.extend(self._generate_compliance_checks(classification))
            lines.append("")
        
        # Approval Workflow
        if template["include_approval_workflow"]:
            lines.extend(self._generate_approval_workflow(classification))
            lines.append("")
        
        # Risk Assessment (for executive template)
        if template.get("include_risk_assessment", False):
            lines.extend(self._generate_risk_assessment(classification, amount))
            lines.append("")
        
        # Footer
        lines.extend(self._generate_footer(metadata))
        
        return "\n".join(lines)
    
    def _generate_voucher_info(self, metadata: VoucherMetadata) -> List[str]:
        """Generate voucher information section."""
        lines = []
        lines.append("VOUCHER INFORMATION:")
        lines.append(f"Voucher Number: {metadata.voucher_number}")
        lines.append(f"Creation Date: {metadata.creation_date}")
        lines.append(f"Created By: {metadata.created_by}")
        lines.append(f"Department: {metadata.department}")
        if metadata.project_code:
            lines.append(f"Project Code: {metadata.project_code}")
        if metadata.due_date:
            lines.append(f"Due Date: {metadata.due_date}")
        return lines
    
    def _generate_account_details(self, account_desc: AccountDescriptions) -> List[str]:
        """Generate account details section."""
        lines = []
        lines.append("ACCOUNT DETAILS:")
        lines.append(f"Entity: {account_desc.entity}")
        lines.append(f"Cost Center: {account_desc.cost_center}")
        lines.append(f"GL Account: {account_desc.gl_account}")
        lines.append(f"Budget Group: {account_desc.budget_group}")
        if hasattr(account_desc, 'future1') and account_desc.future1:
            lines.append(f"Future 1: {account_desc.future1}")
        if hasattr(account_desc, 'future2') and account_desc.future2:
            lines.append(f"Future 2: {account_desc.future2}")
        return lines
    
    def _generate_payment_details(self, amount: float, classification: VoucherClassification) -> List[str]:
        """Generate payment details section."""
        lines = []
        lines.append("PAYMENT DETAILS:")
        amount_str, drcr = self._format_amount_with_type(amount)
        lines.append(f"Amount: {amount_str} ({drcr})")
        lines.append(f"Currency: USD")
        lines.append(f"Payment Method: To be determined")
        lines.append(f"Category: {classification.category}")
        lines.append(f"Subcategory: {classification.subcategory}")
        return lines
    
    def _generate_classification_details(self, classification: VoucherClassification) -> List[str]:
        """Generate classification details section."""
        lines = []
        lines.append("CLASSIFICATION DETAILS:")
        lines.append(f"Category: {classification.category}")
        lines.append(f"Subcategory: {classification.subcategory}")
        lines.append(f"Risk Level: {classification.risk_level}")
        lines.append(f"Approval Level: {classification.approval_level}")
        lines.append(f"Requires Approval: {'Yes' if classification.requires_approval else 'No'}")
        lines.append(f"Business Justification: {classification.business_justification}")
        return lines
    
    def _generate_vendor_info(self, metadata: VoucherMetadata) -> List[str]:
        """Generate vendor information section."""
        lines = []
        lines.append("VENDOR INFORMATION:")
        if metadata.vendor_name:
            lines.append(f"Vendor Name: {metadata.vendor_name}")
        if metadata.vendor_id:
            lines.append(f"Vendor ID: {metadata.vendor_id}")
        if metadata.contract_reference:
            lines.append(f"Contract Reference: {metadata.contract_reference}")
        return lines
    
    def _generate_compliance_checks(self, classification: VoucherClassification) -> List[str]:
        """Generate compliance checks section."""
        lines = []
        lines.append("REQUIRED COMPLIANCE CHECKS:")
        for i, check in enumerate(classification.compliance_checks, 1):
            lines.append(f"{i}. {check.replace('_', ' ').title()}")
        return lines
    
    def _generate_approval_workflow(self, classification: VoucherClassification) -> List[str]:
        """Generate approval workflow section."""
        lines = []
        lines.append("APPROVAL WORKFLOW:")
        
        workflows = {
            "Standard": [
                "1. Department Head Approval",
                "2. Finance Processing"
            ],
            "High": [
                "1. Department Head Approval",
                "2. Finance Director Approval", 
                "3. Finance Processing"
            ],
            "Executive": [
                "1. Department Head Approval",
                "2. Finance Director Approval",
                "3. Executive Approval",
                "4. Finance Processing"
            ]
        }
        
        workflow = workflows.get(classification.approval_level, ["Manual Review Required"])
        lines.extend(workflow)
        return lines
    
    def _generate_risk_assessment(self, classification: VoucherClassification, amount: float) -> List[str]:
        """Generate risk assessment section."""
        lines = []
        lines.append("RISK ASSESSMENT:")
        lines.append(f"Risk Level: {classification.risk_level}")
        lines.append(f"Amount Risk: {'High' if amount >= 100000 else 'Medium' if amount >= 10000 else 'Low'}")
        lines.append(f"Category Risk: {classification.risk_level}")
        
        # Risk mitigation recommendations
        if classification.risk_level == "High" or amount >= 100000:
            lines.append("Risk Mitigation:")
            lines.append("- Additional documentation required")
            lines.append("- Enhanced approval process")
            lines.append("- Post-payment audit recommended")
        
        return lines
    
    def _generate_footer(self, metadata: VoucherMetadata) -> List[str]:
        """Generate footer section."""
        lines = []
        lines.append("")
        lines.append("=" * 50)
        lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("System: Payment Voucher Creation Agent")
        return lines
    
    def _format_amount_with_type(self, amount: float) -> Tuple[str, str]:
        """Format amount with debit/credit type."""
        if amount >= 0:
            return (f"${amount:,.2f}", "Debit")
        return (f"${abs(amount):,.2f}", "Credit")
    
    def generate_batch_vouchers(self, 
                               transactions: List[Dict],
                               template_style: Optional[str] = None) -> str:
        """Generate multiple vouchers in a batch."""
        lines = []
        lines.append("BATCH PAYMENT VOUCHERS")
        lines.append("=" * 50)
        lines.append(f"Batch Date: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append(f"Total Vouchers: {len(transactions)}")
        lines.append("")
        
        for i, transaction in enumerate(transactions, 1):
            lines.append(f"VOUCHER {i} of {len(transactions)}")
            lines.append("-" * 30)
            lines.append(transaction.get('voucher_content', 'Voucher content not available'))
            lines.append("")
            lines.append("=" * 50)
            lines.append("")
        
        return "\n".join(lines)
