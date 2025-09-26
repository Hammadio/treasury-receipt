"""Treasury receipt text generator."""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from .account_parser import AccountDescriptions
from .business_rules import RuleOutcome


def format_amount_with_type(net_amount: float) -> Tuple[str, str]:
    if net_amount >= 0:
        return (f"{net_amount:,.2f}", "Debit")
    return (f"{abs(net_amount):,.2f}", "Credit")


def generate_receipt_block(
    account_desc: AccountDescriptions,
    net_amount: float,
    outcome: RuleOutcome,
) -> str:
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



