#!/usr/bin/env python3
"""
Quick test to verify the Payment Voucher system is working correctly.
"""

import sys
from pathlib import Path

# Add the treasury_receipt_system to the path
sys.path.insert(0, str(Path(__file__).parent / "treasury_receipt_system"))

def test_imports():
    """Test that all modules can be imported successfully."""
    print("Testing imports...")
    
    try:
        from treasury_receipt_system.payment_voucher.processor import PaymentVoucherProcessor
        from treasury_receipt_system.payment_voucher.voucher_classifier import PaymentVoucherClassifier
        from treasury_receipt_system.payment_voucher.voucher_generator import PaymentVoucherGenerator
        from treasury_receipt_system.payment_voucher.approval_workflow import ApprovalWorkflowManager
        from treasury_receipt_system.payment_voucher.voucher_validator import VoucherValidator
        print("✅ All Payment Voucher modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without requiring Excel file."""
    print("\nTesting basic functionality...")
    
    try:
        from treasury_receipt_system.payment_voucher.voucher_classifier import PaymentVoucherClassifier
        from treasury_receipt_system.payment_voucher.voucher_validator import VoucherValidator
        
        # Test classifier
        classifier = PaymentVoucherClassifier(enable_llm=False)
        classification = classifier.classify_transaction("Office Supplies - Stationery", 500.00)
        
        print(f"✅ Classification test passed: {classification.category}")
        
        # Test validator
        validator = VoucherValidator()
        print("✅ Validator initialized successfully")
        
        return True
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

def test_cli_help():
    """Test that CLI help works."""
    print("\nTesting CLI help...")
    
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "treasury_receipt_system.main", "--help"
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0 and "payment_voucher" in result.stdout:
            print("✅ CLI help shows Payment Voucher options")
            return True
        else:
            print("❌ CLI help test failed")
            print(f"Return code: {result.returncode}")
            print(f"Output: {result.stdout}")
            return False
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Payment Voucher System - Quick Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_basic_functionality,
        test_cli_help
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! The Payment Voucher system is ready to use.")
        print("\nNext steps:")
        print("1. Run: python example_payment_voucher_usage.py")
        print("2. Test with your Excel file: python -m treasury_receipt_system.main --mode payment_voucher --excel ADERP_COA_2025.xlsx --input 'test transaction'")
    else:
        print("❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
