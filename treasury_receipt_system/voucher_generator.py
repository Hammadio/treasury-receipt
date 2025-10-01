"""Payment voucher text generator."""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple
from datetime import datetime

from .account_parser import AccountDescriptions
from .business_rules import RuleOutcome


def format_amount_with_type(net_amount: float) -> Tuple[str, str]:
    if net_amount >= 0:
        return (f"{net_amount:,.2f}", "Debit")
    return (f"{abs(net_amount):,.2f}", "Credit")


def generate_payment_voucher_block(
    account_desc: AccountDescriptions,
    net_amount: float,
    outcome: RuleOutcome,
    voucher_number: str = "",
) -> str:
    amount_str, drcr = format_amount_with_type(net_amount)
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    lines: List[str] = []
    lines.append("PAYMENT VOUCHER")
    lines.append("===============")
    lines.append(f"Voucher Number: {voucher_number or 'PV-' + current_date.replace('-', '')}")
    lines.append(f"Date: {current_date}")
    lines.append("")
    lines.append("ACCOUNT DETAILS:")
    lines.append(f"Entity: {account_desc.entity}")
    lines.append(f"Cost Center: {account_desc.cost_center}")
    lines.append(f"GL Account: {account_desc.gl_account}")
    lines.append(f"Budget Group: {account_desc.budget_group}")
    lines.append("")
    lines.append("PAYMENT DETAILS:")
    lines.append(f"Amount: {amount_str} ({drcr})")
    lines.append(f"Transaction Type: {outcome.transaction_type}")
    lines.append(f"Voucher Category: {outcome.voucher_category}")
    lines.append(f"Approval Level Required: {outcome.approval_level}")
    lines.append("")
    lines.append("PROCESSING STATUS:")
    lines.append(
        "Additional Processing Required: "
        + ("Yes" if outcome.additional_processing_required else "No")
    )
    lines.append(f"Reason: {outcome.reason}")
    lines.append("")
    
    # Add approval workflow based on level
    if outcome.approval_level == "Executive":
        lines.append("APPROVAL WORKFLOW:")
        lines.append("1. Department Head Approval")
        lines.append("2. Finance Director Approval")
        lines.append("3. Executive Approval Required")
    elif outcome.approval_level == "High":
        lines.append("APPROVAL WORKFLOW:")
        lines.append("1. Department Head Approval")
        lines.append("2. Finance Director Approval")
    else:
        lines.append("APPROVAL WORKFLOW:")
        lines.append("1. Department Head Approval")
    
    return "\n".join(lines)


def generate_receipt_block(
    account_desc: AccountDescriptions,
    net_amount: float,
    outcome: RuleOutcome,
) -> str:
    """Legacy Treasury Receipt generator for backward compatibility."""
    amount_str, drcr = format_amount_with_type(net_amount)
    lines: List[str] = []
    lines.append("TREASURY RECEIPT")
    lines.append("================")
    lines.append(
        "Account: "
        f"{account_desc.entity} - {account_desc.cost_center} - {account_desc.gl_account} - {account_desc.budget_group}"
    )
    lines.append(f"Amount: {amount_str} ({drcr})")
    lines.append(f"Transaction Type: {outcome.transaction_type}")
    lines.append(
        "Additional Processing Required: "
        + ("Yes" if outcome.additional_processing_required else "No")
    )
    return "\n".join(lines)
