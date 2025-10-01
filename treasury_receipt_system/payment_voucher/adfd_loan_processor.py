"""
ADFD Loan Revenue Processor for Payment Voucher Creation.

This module handles the specialized processing of ADFD loan revenue data
with the specific account structure required for government loan repayments.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path

LOGGER = logging.getLogger(__name__)


@dataclass
class ADFDLoanData:
    """ADFD loan data structure."""
    project_no: str
    country_name: str
    statement_of_shares: str
    total: float


@dataclass
class ADFDLoanGroup:
    """Grouped ADFD loan data by project and country."""
    project_no: str
    country_name: str
    total_amount: float


@dataclass
class ADFDLoanVoucherEntry:
    """Individual voucher entry for ADFD loans."""
    account_name: str
    debit: Optional[float]
    credit: Optional[float]
    description: str


class ADFDLoanProcessor:
    """Processor for ADFD loan revenue data."""
    
    def __init__(self):
        self.loan_data: List[ADFDLoanData] = []
        self.loan_groups: List[ADFDLoanGroup] = []
        self.voucher_entries: List[ADFDLoanVoucherEntry] = []
    
    def load_csv_data(self, csv_file_path: str) -> bool:
        """Load ADFD loan data from CSV file."""
        try:
            self.loan_data = []
            
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Debug: Print column names
                LOGGER.info(f"CSV columns found: {reader.fieldnames}")
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is header
                    LOGGER.debug(f"Processing row {row_num}: {row}")
                    
                    # Only process rows where Statement of Shares = "Total"
                    if row.get('Statement of Shares', '').strip() == 'Total':
                        try:
                            # Handle BOM character in column names
                            project_no = row.get('Project no', '') or row.get('\ufeffProject no', '')
                            
                            loan_data = ADFDLoanData(
                                project_no=project_no.strip(),
                                country_name=row.get('Country Name', '').strip(),
                                statement_of_shares=row.get('Statement of Shares', '').strip(),
                                total=float(row.get('Total', '0').strip())
                            )
                            self.loan_data.append(loan_data)
                            LOGGER.info(f"Added loan data: {loan_data.project_no} - {loan_data.country_name} - {loan_data.total}")
                        except ValueError as e:
                            LOGGER.warning(f"Invalid data in row {row_num}: {row}, error: {e}")
                            continue
                        except KeyError as e:
                            LOGGER.warning(f"Missing column in row {row_num}: {e}, row: {row}")
                            continue
                    else:
                        LOGGER.debug(f"Skipping row {row_num} - not a 'Total' row: {row.get('Statement of Shares', '')}")
            
            LOGGER.info(f"Loaded {len(self.loan_data)} ADFD loan records from {csv_file_path}")
            return len(self.loan_data) > 0
            
        except FileNotFoundError:
            LOGGER.error(f"CSV file not found: {csv_file_path}")
            return False
        except Exception as e:
            LOGGER.error(f"Error loading CSV file: {e}")
            return False
    
    def group_loan_data(self) -> None:
        """Group loan data by project and country."""
        self.loan_groups = []
        
        # Group by project_no and country_name
        grouped_data: Dict[Tuple[str, str], List[ADFDLoanData]] = {}
        
        for loan in self.loan_data:
            key = (loan.project_no, loan.country_name)
            if key not in grouped_data:
                grouped_data[key] = []
            grouped_data[key].append(loan)
        
        # Create loan groups
        for (project_no, country_name), loans in grouped_data.items():
            total_amount = sum(loan.total for loan in loans)
            
            loan_group = ADFDLoanGroup(
                project_no=project_no,
                country_name=country_name,
                total_amount=total_amount
            )
            self.loan_groups.append(loan_group)
        
        LOGGER.info(f"Grouped into {len(self.loan_groups)} loan groups")
    
    def generate_voucher_entries(self) -> None:
        """Generate Payment Voucher entries for ADFD loans."""
        self.voucher_entries = []
        
        if not self.loan_groups:
            LOGGER.warning("No loan groups available for voucher generation")
            return
        
        # Calculate total funding amount (sum of all country totals)
        total_funding = sum(group.total_amount for group in self.loan_groups)
        
        # Create description with project numbers
        project_countries = [f"{group.country_name} Loan {group.project_no}" for group in self.loan_groups]
        description = f"{' & '.join(project_countries)} Repayments - Funding Entries {datetime.now().year}"
        
        # Debug logging
        LOGGER.info(f"Loan groups: {[(g.project_no, g.country_name, g.total_amount) for g in self.loan_groups]}")
        LOGGER.info(f"Project countries: {project_countries}")
        LOGGER.info(f"Final description: {description}")
        
        # 1. Funding entry (Debit)
        funding_entry = ADFDLoanVoucherEntry(
            account_name="Funding- Foreign Loans",
            debit=total_funding,
            credit=None,
            description=description
        )
        self.voucher_entries.append(funding_entry)
        
        # 2. Individual country entries (Credit)
        for group in self.loan_groups:
            country_entry = ADFDLoanVoucherEntry(
                account_name=f"Loans-{group.country_name}",
                debit=None,
                credit=group.total_amount,
                description=description
            )
            self.voucher_entries.append(country_entry)
        
        LOGGER.info(f"Generated {len(self.voucher_entries)} voucher entries")
    
    def generate_payment_voucher_csv(self) -> str:
        """Generate Payment Voucher in CSV format."""
        if not self.voucher_entries:
            return "No voucher entries available"
        
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # CSV Header
        writer.writerow(["Acc No & Acc Name", "Debit", "Credit", "Description"])
        
        # Voucher entries
        for entry in self.voucher_entries:
            debit_value = f"{entry.debit:,.2f}" if entry.debit is not None else ""
            credit_value = f"{entry.credit:,.2f}" if entry.credit is not None else ""
            
            writer.writerow([
                entry.account_name,
                debit_value,
                credit_value,
                entry.description
            ])
        
        # Summary row
        total_debit = sum(entry.debit for entry in self.voucher_entries if entry.debit is not None)
        total_credit = sum(entry.credit for entry in self.voucher_entries if entry.credit is not None)
        
        writer.writerow([
            "TOTAL",
            f"{total_debit:,.2f}",
            f"{total_credit:,.2f}",
            f"Balanced: {'Yes' if abs(total_debit - total_credit) < 0.01 else 'No'}"
        ])
        
        return output.getvalue()
    
    def generate_payment_voucher(self) -> str:
        """Generate Payment Voucher in the required format (legacy method)."""
        if not self.voucher_entries:
            return "No voucher entries available"
        
        lines = []
        
        # Header
        lines.append("PAYMENT VOUCHER - ADFD LOAN REVENUES")
        lines.append("=" * 60)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Total Entries: {len(self.voucher_entries)}")
        lines.append("")
        
        # Table header
        lines.append("Acc No & Acc Name".ljust(30) + "Debit".ljust(15) + "Credit".ljust(15) + "Description")
        lines.append("-" * 80)
        
        # Voucher entries
        for entry in self.voucher_entries:
            account = entry.account_name.ljust(30)
            debit = f"{entry.debit:,.2f}" if entry.debit is not None else "".ljust(15)
            credit = f"{entry.credit:,.2f}" if entry.credit is not None else "".ljust(15)
            description = entry.description
            
            lines.append(f"{account}{debit}{credit}{description}")
        
        # Summary
        total_debit = sum(entry.debit for entry in self.voucher_entries if entry.debit is not None)
        total_credit = sum(entry.credit for entry in self.voucher_entries if entry.credit is not None)
        
        lines.append("-" * 80)
        lines.append(f"{'TOTAL'.ljust(30)}{total_debit:,.2f}".ljust(45) + f"{total_credit:,.2f}")
        
        # Validation
        if abs(total_debit - total_credit) < 0.01:  # Allow for small rounding differences
            lines.append("")
            lines.append("✅ Voucher is balanced")
        else:
            lines.append("")
            lines.append(f"❌ Voucher is not balanced (Difference: {abs(total_debit - total_credit):,.2f})")
        
        return "\n".join(lines)
    
    def process_adfd_loans(self, csv_file_path: str, output_format: str = "csv") -> str:
        """Complete ADFD loan processing pipeline."""
        LOGGER.info("Starting ADFD loan processing")
        
        # Load data
        if not self.load_csv_data(csv_file_path):
            return "Error: Could not load CSV data"
        
        # Group data
        self.group_loan_data()
        
        if not self.loan_groups:
            return "No loan data found to process"
        
        # Generate voucher entries
        self.generate_voucher_entries()
        
        # Generate Payment Voucher in requested format
        if output_format.lower() == "csv":
            voucher = self.generate_payment_voucher_csv()
        else:
            voucher = self.generate_payment_voucher()
        
        LOGGER.info("ADFD loan processing completed")
        return voucher
    
    def get_processing_summary(self) -> Dict:
        """Get summary of processing results."""
        return {
            "total_records_loaded": len(self.loan_data),
            "total_loan_groups": len(self.loan_groups),
            "total_voucher_entries": len(self.voucher_entries),
            "total_funding_amount": sum(group.total_amount for group in self.loan_groups),
            "countries": [group.country_name for group in self.loan_groups],
            "projects": [group.project_no for group in self.loan_groups]
        }


def process_adfd_csv_file(csv_file_path: str) -> str:
    """Convenience function to process ADFD CSV file."""
    processor = ADFDLoanProcessor()
    return processor.process_adfd_loans(csv_file_path)


if __name__ == "__main__":
    # Test the processor
    csv_file = "inputs_loan_revenues_ADFD_Dummy.csv"
    result = process_adfd_csv_file(csv_file)
    print(result)
