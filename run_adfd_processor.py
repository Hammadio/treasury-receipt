#!/usr/bin/env python3
"""
ADFD Loan Revenue Processor - Main Script

This script processes ADFD loan revenue CSV files and generates Payment Vouchers
with the specific account structure required for government loan repayments.
"""

import sys
import logging
from pathlib import Path

# Add the treasury_receipt_system to the path
sys.path.insert(0, str(Path(__file__).parent / "treasury_receipt_system"))

from treasury_receipt_system.payment_voucher.adfd_loan_processor import ADFDLoanProcessor

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG to see more details
    format='%(asctime)s | %(levelname)s | %(message)s'
)

LOGGER = logging.getLogger(__name__)


def main():
    """Main function to process ADFD loan data."""
    print("ADFD Loan Revenue Processor")
    print("=" * 50)
    
    # Input file path
    csv_file = "inputs_loan_revenues_ADFD_Dummy.csv"
    
    # Check if file exists
    if not Path(csv_file).exists():
        print(f"❌ Error: CSV file '{csv_file}' not found")
        print("Please make sure the file exists in the current directory")
        return
    
    print(f"📁 Processing file: {csv_file}")
    print()
    
    # Create processor and process the file
    processor = ADFDLoanProcessor()
    
    try:
        # Process the ADFD loan data (CSV format)
        result = processor.process_adfd_loans(csv_file, output_format="csv")
        
        # Display the result
        print("Generated Payment Voucher (CSV format):")
        print("-" * 50)
        print(result)
        
        # Show processing summary
        summary = processor.get_processing_summary()
        print("\n" + "=" * 50)
        print("PROCESSING SUMMARY")
        print("=" * 50)
        print(f"📊 Total records loaded: {summary['total_records_loaded']}")
        print(f"🌍 Countries processed: {', '.join(summary['countries'])}")
        print(f"📋 Projects processed: {', '.join(summary['projects'])}")
        print(f"💰 Total funding amount: ${summary['total_funding_amount']:,.2f}")
        print(f"📝 Voucher entries generated: {summary['total_voucher_entries']}")
        
        # Save output to CSV file
        output_file = "adfd_payment_voucher_output.csv"
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            f.write(result)
        
        print(f"\n💾 Output saved to: {output_file}")
        print("\n✅ Processing completed successfully!")
        
    except Exception as e:
        print(f"❌ Error processing ADFD loan data: {e}")
        LOGGER.error(f"Processing error: {e}", exc_info=True)


if __name__ == "__main__":
    main()