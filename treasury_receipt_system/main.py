"""Main application entry point for Treasury Receipt Automation System."""

from __future__ import annotations

import argparse
import os
import logging
from collections import defaultdict
from typing import Dict, List, Tuple
import pandas as pd

# Global toggle set by CLI
_ENABLE_LLM = True

from .account_parser import AccountParser
from .business_rules import BusinessRules
from .receipt_generator import generate_receipt_block
from .reference_lookup import ReferenceLookup
from .utils import Transaction, configure_logging


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
    reference = ReferenceLookup.from_excel(excel_path)
    parser = AccountParser(reference)
    rules = BusinessRules(enable_llm=_ENABLE_LLM)

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
        blocks.append(generate_receipt_block(acc_desc, net_amount, outcome))

    return "\n\n".join(blocks)


def main() -> None:
    argp = argparse.ArgumentParser(description="Treasury Receipt Automation System")
    argp.add_argument("--excel", required=True, help="Path to ADERP_COA_2025.xlsx")
    argp.add_argument("--input", required=False, help="Inline input text of transactions")
    argp.add_argument("--input-file", required=False, help="Path to a text file with transactions")
    argp.add_argument("--output-file", required=False, help="Write receipt output to this .txt file")
    argp.add_argument("--no-llm", action="store_true", help="Disable local LLM classification")
    argp.add_argument("--inspect-excel", action="store_true", help="List sheets and columns then exit")
    argp.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = argp.parse_args()

    configure_logging(logging.DEBUG if args.debug else logging.INFO)

    if args.input_file:
        with open(args.input_file, "r", encoding="utf-8") as fh:
            input_text = fh.read()
    else:
        input_text = args.input or ""

    global _ENABLE_LLM
    _ENABLE_LLM = not args.no_llm

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

    # Console note about LLM usage
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
        print(f"Receipt written successfully to: {args.output_file}")
    else:
        print(output)


if __name__ == "__main__":
    main()


