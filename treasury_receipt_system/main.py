"""Main application entry point for Treasury Receipt Automation System."""

from __future__ import annotations

import argparse
import os
import logging
from collections import defaultdict
from typing import Dict, List, Tuple
from datetime import datetime
import pandas as pd

# Global toggles set by CLI
_ENABLE_LLM = True
_SYSTEM_MODE = "treasury_receipt"  # "treasury_receipt" or "payment_voucher"

from .account_parser import AccountParser
from .business_rules import BusinessRules
from .receipt_generator import generate_receipt_block
from .voucher_generator import generate_payment_voucher_block, generate_receipt_block as legacy_generate_receipt_block
from .reference_lookup import ReferenceLookup
from .utils import Transaction, configure_logging
from .payment_voucher.processor import PaymentVoucherProcessor


LOGGER = logging.getLogger(__name__)


def group_transactions_first4(transactions: List[Transaction]) -> Dict[Tuple[str, str, str, str], List[Transaction]]:
    grouped: Dict[Tuple[str, str, str, str], List[Transaction]] = defaultdict(list)
    for t in transactions:
        grouped[t.parsed_account.key_first4()].append(t)
    return grouped


def compute_net_amount(transactions: List[Transaction]) -> float:
    net = 0.0
    for t in transactions:
        signed = t.amount if t.is_debit else -t.amount
        net += signed
    return net


def process_transactions(excel_path: str, input_text: str) -> str:
    if _SYSTEM_MODE == "payment_voucher":
        return process_payment_vouchers(excel_path, input_text)
    else:
        return process_treasury_receipts(excel_path, input_text)


def process_treasury_receipts(excel_path: str, input_text: str) -> str:
    """Process transactions for Treasury Receipts (legacy functionality)."""
    reference = ReferenceLookup.from_excel(excel_path)
    parser = AccountParser(reference)
    rules = BusinessRules(enable_llm=_ENABLE_LLM, system_mode=_SYSTEM_MODE)

    txns = parser.parse_text_transactions(input_text)
    if not txns:
        return "No valid transactions found in input."

    # Validate and flag errors
    validation_errors: List[str] = []
    for t in txns:
        is_valid, errors = parser.validate_account(t.parsed_account)
        if not is_valid:
            validation_errors.extend([f"{t.raw_line} -> {e}" for e in errors])
    if validation_errors:
        header = "Validation errors detected:\n" + "\n".join(validation_errors)
        LOGGER.error(header)
        # Continue processing but prepend errors to output
    else:
        header = ""

    grouped = group_transactions_first4(txns)

    blocks: List[str] = []
    if header:
        blocks.append(header)

    for key, items in grouped.items():
        first = items[0]
        acc_desc = parser.lookup_descriptions(first.parsed_account)
        net_amount = compute_net_amount(items)
        outcome = rules.classify_transaction(acc_desc.gl_account, net_amount)
        blocks.append(legacy_generate_receipt_block(acc_desc, net_amount, outcome))

    return "\n\n".join(blocks)


def process_payment_vouchers(excel_path: str, input_text: str) -> str:
    """Process transactions for Payment Vouchers using new modular system."""
    processor = PaymentVoucherProcessor(enable_llm=_ENABLE_LLM)
    
    result = processor.process_transactions(
        excel_path=excel_path,
        input_text=input_text,
        created_by="System User",
        department="Finance",
        template_style="standard"
    )
    
    if not result["success"]:
        error_msg = "Payment Voucher processing failed:\n"
        error_msg += "\n".join(result["errors"])
        return error_msg
    
    # Generate output
    blocks = []
    
    # Add summary
    summary = result["summary"]
    blocks.append("PAYMENT VOUCHER PROCESSING SUMMARY")
    blocks.append("=" * 50)
    blocks.append(f"Total Vouchers: {summary['total_vouchers']}")
    blocks.append(f"Total Amount: ${summary['total_amount']:,.2f}")
    blocks.append(f"Processing Errors: {summary['total_errors']}")
    blocks.append("")
    
    # Add individual vouchers
    for voucher in result["vouchers"]:
        blocks.append(voucher["content"])
        blocks.append("")
    
    return "\n".join(blocks)


def main() -> None:
    argp = argparse.ArgumentParser(description="Treasury Receipt / Payment Voucher Automation System")
    argp.add_argument("--excel", required=True, help="Path to ADERP_COA_2025.xlsx")
    argp.add_argument("--input", required=False, help="Inline input text of transactions")
    argp.add_argument("--input-file", required=False, help="Path to a text file with transactions")
    argp.add_argument("--output-file", required=False, help="Write output to this .txt file")
    argp.add_argument("--no-llm", action="store_true", help="Disable local LLM classification")
    argp.add_argument("--mode", choices=["treasury_receipt", "payment_voucher"], default="treasury_receipt", 
                     help="System mode: treasury_receipt or payment_voucher")
    argp.add_argument("--inspect-excel", action="store_true", help="List sheets and columns then exit")
    argp.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = argp.parse_args()

    configure_logging(logging.DEBUG if args.debug else logging.INFO)

    if args.input_file:
        with open(args.input_file, "r", encoding="utf-8") as fh:
            input_text = fh.read()
    else:
        input_text = args.input or ""

    global _ENABLE_LLM, _SYSTEM_MODE
    _ENABLE_LLM = not args.no_llm
    _SYSTEM_MODE = args.mode

    # Inspect mode: list sheets and columns, then exit
    if args.inspect_excel:
        xls = pd.ExcelFile(args.excel, engine="openpyxl")
        print(f"Excel file: {args.excel}")
        print("Sheets and columns:")
        for sheet in xls.sheet_names:
            df = xls.parse(sheet_name=sheet, nrows=5)
            cols = [str(c) for c in df.columns]
            print(f"- {sheet}: {', '.join(cols)}")
        return

    # Console note about system configuration
    print(f"System Mode: {_SYSTEM_MODE}")
    if _ENABLE_LLM:
        model_name = os.getenv("LLM_MODEL", "Qwen3-8B-Instruct")
        endpoint = os.getenv("LLM_ENDPOINT", "")
        if endpoint:
            print(f"LLM enabled: model={model_name}, endpoint={endpoint}")
        else:
            print(f"LLM enabled: model={model_name}, endpoint not set (will likely fall back)")
    else:
        print("LLM disabled: using heuristic classification")

    output = process_transactions(args.excel, input_text)
    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as fh:
            fh.write(output)
        output_type = "Payment Voucher" if _SYSTEM_MODE == "payment_voucher" else "Treasury Receipt"
        print(f"{output_type} written successfully to: {args.output_file}")
    else:
        print(output)


if __name__ == "__main__":
    main()


