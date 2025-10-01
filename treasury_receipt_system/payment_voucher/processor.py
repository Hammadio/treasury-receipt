"""Main Payment Voucher processor that integrates all modules."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

from ..account_parser import AccountParser, AccountDescriptions
from ..reference_lookup import ReferenceLookup
from ..utils import Transaction
from .voucher_classifier import PaymentVoucherClassifier, VoucherClassification
from .voucher_generator import PaymentVoucherGenerator, VoucherMetadata
from .approval_workflow import ApprovalWorkflowManager, ApprovalLevel
from .voucher_validator import VoucherValidator, ValidationResult

LOGGER = logging.getLogger(__name__)


class PaymentVoucherProcessor:
    """Main processor for Payment Voucher creation and management."""
    
    def __init__(self, enable_llm: bool = True, llm_endpoint: Optional[str] = None):
        self.classifier = PaymentVoucherClassifier(enable_llm, llm_endpoint)
        self.generator = PaymentVoucherGenerator()
        self.workflow_manager = ApprovalWorkflowManager()
        self.validator = VoucherValidator()
        
        # Processing statistics
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "by_category": defaultdict(int),
            "by_approval_level": defaultdict(int)
        }
    
    def process_transactions(self, 
                           excel_path: str, 
                           input_text: str,
                           created_by: str = "System",
                           department: str = "Finance",
                           template_style: str = "standard") -> Dict:
        """Process transactions and generate Payment Vouchers."""
        
        LOGGER.info("Starting Payment Voucher processing")
        
        # Load reference data
        reference = ReferenceLookup.from_excel(excel_path)
        parser = AccountParser(reference)
        
        # Parse transactions
        transactions = parser.parse_text_transactions(input_text)
        if not transactions:
            return {
                "success": False,
                "error": "No valid transactions found in input",
                "vouchers": [],
                "statistics": self.stats
            }
        
        # Group transactions
        grouped_transactions = self._group_transactions(transactions)
        
        # Process each group
        vouchers = []
        processing_errors = []
        
        for group_key, group_transactions in grouped_transactions.items():
            try:
                voucher_result = self._process_transaction_group(
                    group_transactions, parser, created_by, department, template_style
                )
                if voucher_result["success"]:
                    vouchers.append(voucher_result["voucher"])
                    self.stats["successful"] += 1
                else:
                    processing_errors.append(voucher_result["error"])
                    self.stats["failed"] += 1
                
                self.stats["total_processed"] += 1
                
            except Exception as exc:
                error_msg = f"Error processing group {group_key}: {str(exc)}"
                LOGGER.error(error_msg)
                processing_errors.append(error_msg)
                self.stats["failed"] += 1
                self.stats["total_processed"] += 1
        
        # Generate summary
        success = len(processing_errors) == 0
        summary = self._generate_processing_summary(vouchers, processing_errors)
        
        return {
            "success": success,
            "vouchers": vouchers,
            "errors": processing_errors,
            "summary": summary,
            "statistics": self.stats
        }
    
    def _group_transactions(self, transactions: List[Transaction]) -> Dict[Tuple, List[Transaction]]:
        """Group transactions by first 4 COA segments."""
        grouped = defaultdict(list)
        for transaction in transactions:
            key = transaction.parsed_account.key_first4()
            grouped[key].append(transaction)
        return dict(grouped)
    
    def _process_transaction_group(self, 
                                  transactions: List[Transaction],
                                  parser: AccountParser,
                                  created_by: str,
                                  department: str,
                                  template_style: str) -> Dict:
        """Process a single group of transactions into a Payment Voucher."""
        
        # Get account descriptions
        first_transaction = transactions[0]
        account_desc = parser.lookup_descriptions(first_transaction.parsed_account)
        
        # Calculate net amount
        net_amount = self._calculate_net_amount(transactions)
        
        # Classify transaction
        classification = self.classifier.classify_transaction(
            account_desc.gl_account, 
            net_amount,
            additional_context={"raw_transactions": [t.raw_line for t in transactions]}
        )
        
        # Validate voucher
        validation_result = self.validator.validate_voucher(
            account_desc, net_amount, classification
        )
        
        # Update statistics
        self.stats["by_category"][classification.category] += 1
        self.stats["by_approval_level"][classification.approval_level] += 1
        
        # Create voucher metadata
        voucher_number = self._generate_voucher_number()
        metadata = VoucherMetadata(
            voucher_number=voucher_number,
            creation_date=datetime.now().strftime("%Y-%m-%d"),
            created_by=created_by,
            department=department
        )
        
        # Generate voucher content
        voucher_content = self.generator.generate_voucher(
            account_desc, net_amount, classification, metadata, template_style
        )
        
        # Create approval workflow if required
        approval_workflow = None
        if classification.requires_approval:
            approval_level = self._map_approval_level(classification.approval_level)
            approval_workflow = self.workflow_manager.create_workflow(
                voucher_number, approval_level, net_amount, created_by
            )
        
        return {
            "success": True,
            "voucher": {
                "voucher_number": voucher_number,
                "content": voucher_content,
                "classification": classification,
                "validation": validation_result,
                "approval_workflow": approval_workflow,
                "metadata": metadata,
                "account_details": account_desc,
                "amount": net_amount,
                "transaction_count": len(transactions)
            }
        }
    
    def _calculate_net_amount(self, transactions: List[Transaction]) -> float:
        """Calculate net amount from transactions."""
        net = 0.0
        for transaction in transactions:
            signed_amount = transaction.amount if transaction.is_debit else -transaction.amount
            net += signed_amount
        return net
    
    def _generate_voucher_number(self) -> str:
        """Generate unique voucher number."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"PV-{timestamp}"
    
    def _map_approval_level(self, level: str) -> ApprovalLevel:
        """Map string approval level to enum."""
        mapping = {
            "Standard": ApprovalLevel.STANDARD,
            "High": ApprovalLevel.HIGH,
            "Executive": ApprovalLevel.EXECUTIVE
        }
        return mapping.get(level, ApprovalLevel.STANDARD)
    
    def _generate_processing_summary(self, 
                                   vouchers: List[Dict], 
                                   errors: List[str]) -> Dict:
        """Generate processing summary."""
        total_amount = sum(v["amount"] for v in vouchers)
        
        # Category breakdown
        category_breakdown = defaultdict(int)
        for voucher in vouchers:
            category_breakdown[voucher["classification"].category] += 1
        
        # Approval level breakdown
        approval_breakdown = defaultdict(int)
        for voucher in vouchers:
            approval_breakdown[voucher["classification"].approval_level] += 1
        
        # Validation summary
        validation_summary = self.validator.get_validation_summary({
            v["voucher_number"]: v["validation"] for v in vouchers
        })
        
        return {
            "total_vouchers": len(vouchers),
            "total_amount": total_amount,
            "total_errors": len(errors),
            "category_breakdown": dict(category_breakdown),
            "approval_breakdown": dict(approval_breakdown),
            "validation_summary": validation_summary,
            "processing_timestamp": datetime.now().isoformat()
        }
    
    def get_voucher_status(self, voucher_number: str) -> Optional[Dict]:
        """Get status of a specific voucher."""
        # This would typically query a database or storage system
        # For now, return a placeholder
        return {
            "voucher_number": voucher_number,
            "status": "processed",
            "last_updated": datetime.now().isoformat()
        }
    
    def approve_voucher(self, voucher_number: str, approver_name: str, 
                       step_id: str, comments: Optional[str] = None) -> bool:
        """Approve a voucher step."""
        # This would typically retrieve the workflow from storage
        # For now, return a placeholder
        LOGGER.info(f"Approval request for voucher {voucher_number} by {approver_name}")
        return True
    
    def get_processing_statistics(self) -> Dict:
        """Get processing statistics."""
        return {
            "statistics": self.stats,
            "success_rate": f"{(self.stats['successful']/max(self.stats['total_processed'], 1))*100:.1f}%",
            "last_updated": datetime.now().isoformat()
        }
    
    def export_vouchers(self, vouchers: List[Dict], format: str = "text") -> str:
        """Export vouchers in specified format."""
        if format == "text":
            return self.generator.generate_batch_vouchers(vouchers)
        elif format == "csv":
            return self._export_csv(vouchers)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_csv(self, vouchers: List[Dict]) -> str:
        """Export vouchers as CSV."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Voucher Number", "Amount", "Category", "Subcategory", 
            "Approval Level", "Status", "Created Date"
        ])
        
        # Data
        for voucher in vouchers:
            writer.writerow([
                voucher["voucher_number"],
                voucher["amount"],
                voucher["classification"].category,
                voucher["classification"].subcategory,
                voucher["classification"].approval_level,
                "Processed",
                voucher["metadata"].creation_date
            ])
        
        return output.getvalue()
