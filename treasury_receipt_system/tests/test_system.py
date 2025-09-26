from __future__ import annotations

import os
import tempfile

import pandas as pd

from treasury_receipt_system.main import process_transactions


def build_test_excel(path: str) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame({
            "Entity": ["201"],
            "Entity Description": ["Department of Finance"],
        }).to_excel(writer, sheet_name="Entity", index=False)

        pd.DataFrame({
            "Cost Center": ["2010023", "2010026"],
            "Cost Center Description": ["Treasury Ops", "Debt Management"],
        }).to_excel(writer, sheet_name="Cost Center", index=False)

        pd.DataFrame({
            "GL Account": ["102148", "331520"],
            "GL Account Description": ["Interest Income - Deposits", "Loan Principal Repayment"],
        }).to_excel(writer, sheet_name="GL Account", index=False)

        pd.DataFrame({
            "Budget Group": ["1"],
            "Budget Group Description": ["Operational"],
        }).to_excel(writer, sheet_name="Budget Group", index=False)

        pd.DataFrame({
            "Future Code": ["000000", "201613"],
            "Future Description": ["N/A", "Loan Identifier 201613"],
        }).to_excel(writer, sheet_name="Futures", index=False)


def test_end_to_end():
    with tempfile.TemporaryDirectory() as tmp:
        xlsx = os.path.join(tmp, "ADERP_COA_2025.xlsx")
        build_test_excel(xlsx)
        input_text = (
            "201.2010023.102148.1.000000.000000.000000 - Debit: 50,000\n"
            "201.2010026.331520.1.000000.201613.000000 - Credit: 25,000\n"
        )
        output = process_transactions(xlsx, input_text)
        assert "TREASURY RECEIPT" in output
        assert "Interest" in output
        assert "Principal Repayment" in output


def test_malformed_input_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        xlsx = os.path.join(tmp, "ADERP_COA_2025.xlsx")
        build_test_excel(xlsx)
        bad_input = "201.2010023.XXX.1.000000.000000.000000 - Debit: 100"
        try:
            process_transactions(xlsx, bad_input)
            assert False, "Expected ValueError for malformed account"
        except ValueError:
            pass



