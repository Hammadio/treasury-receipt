#!/usr/bin/env python3
"""
Example usage of the Payment Voucher Creation Agent.

This script demonstrates how to use the new modular Payment Voucher system
while maintaining compatibility with the existing Treasury Receipt functionality.
"""

import sys
import os
from pathlib import Path

# Add the treasury_receipt_system to the path
sys.path.insert(0, str(Path(__file__).parent / "treasury_receipt_system"))

from treasury_receipt_system.payment_voucher.processor import PaymentVoucherProcessor
from treasury_receipt_system.payment_voucher.voucher_classifier import PaymentVoucherClassifier
from treasury_receipt_system.payment_voucher.voucher_generator import PaymentVoucherGenerator, VoucherMetadata
from treasury_receipt_system.payment_voucher.approval_workflow import ApprovalWorkflowManager, ApprovalLevel
from treasury_receipt_system.payment_voucher.voucher_validator import VoucherValidator


def example_basic_usage():
    """Example of basic Payment Voucher processing."""
    print("=== Basic Payment Voucher Processing ===")
    
    # Sample transaction data
    sample_input = """
201.2010023.102148.1.000000.000000.000000 - Debit: 5000.00
201.2010026.394686.1.000000.000000.000000 - Credit: 2500.00
201.2010026.331520.1.000000.201613.000000 - Credit: 1500.00
201.2010026.394586.1.000000.000000.000000 - Credit: 1000.00
    """.strip()
    
    # Initialize processor
    processor = PaymentVoucherProcessor(enable_llm=False)  # Disable LLM for demo
    
    # Process transactions
    result = processor.process_transactions(
        excel_path="ADERP_COA_2025.xlsx",
        input_text=sample_input,
        created_by="Demo User",
        department="Finance",
        template_style="standard"
    )
    
    if result["success"]:
        print(f"✅ Successfully processed {result['summary']['total_vouchers']} vouchers")
        print(f"💰 Total Amount: ${result['summary']['total_amount']:,.2f}")
        print("\n--- Generated Vouchers ---")
        for voucher in result["vouchers"]:
            print(f"Voucher: {voucher['voucher_number']}")
            print(f"Category: {voucher['classification'].category}")
            print(f"Amount: ${voucher['amount']:,.2f}")
            print(f"Approval Level: {voucher['classification'].approval_level}")
            print("---")
    else:
        print("❌ Processing failed:")
        for error in result["errors"]:
            print(f"  - {error}")


def example_advanced_classification():
    """Example of advanced classification features."""
    print("\n=== Advanced Classification Example ===")
    
    classifier = PaymentVoucherClassifier(enable_llm=False)
    
    # Test different transaction types
    test_cases = [
        ("Office Supplies - Stationery and Paper", 500.00),
        ("Computer Equipment - Laptops and Desktops", 15000.00),
        ("Vendor Payment - Professional Services", 25000.00),
        ("Employee Salary - Monthly Compensation", 8000.00),
        ("Administrative Overhead - General Office", 2000.00)
    ]
    
    for description, amount in test_cases:
        classification = classifier.classify_transaction(description, amount)
        print(f"Description: {description}")
        print(f"Amount: ${amount:,.2f}")
        print(f"Category: {classification.category}")
        print(f"Subcategory: {classification.subcategory}")
        print(f"Approval Level: {classification.approval_level}")
        print(f"Risk Level: {classification.risk_level}")
        print(f"Compliance Checks: {', '.join(classification.compliance_checks)}")
        print("---")


def example_validation():
    """Example of voucher validation."""
    print("\n=== Voucher Validation Example ===")
    
    validator = VoucherValidator()
    
    # Mock account description and classification
    from treasury_receipt_system.account_parser import AccountDescriptions
    from treasury_receipt_system.payment_voucher.voucher_classifier import VoucherClassification
    
    account_desc = AccountDescriptions(
        entity="201",
        cost_center="2010023",
        gl_account="102148",
        budget_group="1",
        future1="000000",
        future2="000000",
        future3="000000"
    )
    
    classification = VoucherClassification(
        category="Operating",
        subcategory="Office Supplies",
        approval_level="Standard",
        requires_approval=False,
        business_justification="Office supplies for daily operations",
        risk_level="Low",
        compliance_checks=["budget_approval", "receipt_verification"]
    )
    
    # Validate voucher
    validation_result = validator.validate_voucher(
        account_desc=account_desc,
        amount=5000.00,
        classification=classification
    )
    
    print(f"Valid: {'✅' if validation_result.is_valid else '❌'}")
    print(f"Errors: {len(validation_result.errors)}")
    print(f"Warnings: {len(validation_result.warnings)}")
    print(f"Compliance Checks: {len(validation_result.compliance_checks)}")
    print(f"Recommendations: {len(validation_result.recommendations)}")
    
    if validation_result.errors:
        print("Errors:")
        for error in validation_result.errors:
            print(f"  - {error}")
    
    if validation_result.warnings:
        print("Warnings:")
        for warning in validation_result.warnings:
            print(f"  - {warning}")


def example_approval_workflow():
    """Example of approval workflow management."""
    print("\n=== Approval Workflow Example ===")
    
    workflow_manager = ApprovalWorkflowManager()
    
    # Create a workflow for a high-value transaction
    workflow = workflow_manager.create_workflow(
        voucher_number="PV-20241201-001",
        approval_level=ApprovalLevel.HIGH,
        amount=75000.00,
        created_by="Finance User"
    )
    
    print(f"Created workflow: {workflow.workflow_id}")
    print(f"Total steps: {workflow.total_steps}")
    print(f"Current step: {workflow.current_step}")
    print(f"Status: {workflow.status.value}")
    
    # Get workflow status
    status = workflow_manager.get_workflow_status(workflow)
    print(f"Progress: {status['progress']}")
    print(f"Next approver: {workflow_manager.get_next_approver(workflow)}")
    
    # Simulate approval
    success = workflow_manager.approve_step(
        workflow=workflow,
        step_id="dept_head",
        approver_name="John Smith",
        comments="Approved for department budget"
    )
    
    print(f"Approval result: {'✅' if success else '❌'}")
    print(f"New status: {workflow.status.value}")
    print(f"Current step: {workflow.current_step}")


def example_custom_voucher_generation():
    """Example of custom voucher generation."""
    print("\n=== Custom Voucher Generation Example ===")
    
    generator = PaymentVoucherGenerator(template_style="executive")
    
    # Mock data
    from treasury_receipt_system.account_parser import AccountDescriptions
    from treasury_receipt_system.payment_voucher.voucher_classifier import VoucherClassification
    
    account_desc = AccountDescriptions(
        entity="201",
        cost_center="2010023",
        gl_account="102148",
        budget_group="1",
        future1="000000",
        future2="000000",
        future3="000000"
    )
    
    classification = VoucherClassification(
        category="Capital",
        subcategory="IT Equipment",
        approval_level="Executive",
        requires_approval=True,
        business_justification="IT infrastructure upgrade",
        risk_level="Medium",
        compliance_checks=["asset_approval", "depreciation_setup", "budget_approval"]
    )
    
    metadata = VoucherMetadata(
        voucher_number="PV-20241201-EXEC-001",
        creation_date="2024-12-01",
        created_by="IT Department",
        department="Information Technology",
        project_code="IT-UPGRADE-2024",
        vendor_name="Tech Solutions Inc.",
        vendor_id="VEND-001",
        contract_reference="CONTRACT-IT-2024-001",
        due_date="2024-12-15"
    )
    
    # Generate voucher
    voucher_content = generator.generate_voucher(
        account_desc=account_desc,
        amount=150000.00,
        classification=classification,
        metadata=metadata,
        template_style="executive"
    )
    
    print("Generated Executive Payment Voucher:")
    print("=" * 60)
    print(voucher_content)


def main():
    """Run all examples."""
    print("Payment Voucher Creation Agent - Usage Examples")
    print("=" * 60)
    
    try:
        example_basic_usage()
        example_advanced_classification()
        example_validation()
        example_approval_workflow()
        example_custom_voucher_generation()
        
        print("\n✅ All examples completed successfully!")
        print("\nTo use the Payment Voucher system in production:")
        print("1. Run: python -m treasury_receipt_system.main --mode payment_voucher --excel ADERP_COA_2025.xlsx --input-file sample_input_payment_voucher.txt")
        print("2. Or use the PaymentVoucherProcessor class directly in your code")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        print("Make sure you have the required dependencies installed:")
        print("pip install -r requirements.txt")


if __name__ == "__main__":
    main()
