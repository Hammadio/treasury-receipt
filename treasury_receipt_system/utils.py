"""Utility helpers for the Treasury Receipt system.

This module provides:
- Logging configuration
- Common dataclasses and types
- Text parsing helpers
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logger for the application.

    Parameters
    ----------
    level: int
        Logging level, e.g., logging.INFO or logging.DEBUG
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


ACCOUNT_SEGMENT_PATTERN = re.compile(
    r"^(?P<entity>\d{3})\.(?P<cost_center>\d{7})\.(?P<gl_account>\d{6})\.(?P<budget_group>\d)\.(?P<future1>\d{6})\.(?P<future2>\d{6})\.(?P<future3>\d{6})$"
)


AMOUNT_LINE_PATTERN = re.compile(
    r"(?P<account>[0-9\.]{10,})\s*[-–—]\s*(?P<type>Debit|Credit)\s*:\s*(?P<amount>[\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedAccount:
    entity: str
    cost_center: str
    gl_account: str
    budget_group: str
    future1: str
    future2: str
    future3: str

    def key_first4(self) -> Tuple[str, str, str, str]:
        return (self.entity, self.cost_center, self.gl_account, self.budget_group)


@dataclass
class Transaction:
    parsed_account: ParsedAccount
    amount: float
    is_debit: bool
    raw_line: str


def parse_amount(value: str) -> float:
    """Parse an amount string like "50,000.00" into float.

    Raises ValueError if the value cannot be parsed.
    """
    normalized = value.replace(",", "").strip()
    return float(normalized)


def parse_transaction_lines(text: str) -> List[Transaction]:
    """Parse free-form text input into a list of Transaction objects.

    Accepts lines containing account number followed by "- Debit:" or "- Credit:"
    and an amount. Ignores empty lines and lines without a valid pattern.
    """
    transactions: List[Transaction] = []
    for line in text.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        match = AMOUNT_LINE_PATTERN.search(candidate)
        if not match:
            continue
        account = match.group("account").strip()
        ttype = match.group("type").strip().lower()
        amount = parse_amount(match.group("amount"))

        acc_match = ACCOUNT_SEGMENT_PATTERN.match(account)
        if not acc_match:
            raise ValueError(f"Malformed account number: {account}")

        parts = acc_match.groupdict()
        parsed = ParsedAccount(
            entity=parts["entity"],
            cost_center=parts["cost_center"],
            gl_account=parts["gl_account"],
            budget_group=parts["budget_group"],
            future1=parts["future1"],
            future2=parts["future2"],
            future3=parts["future3"],
        )
        transactions.append(
            Transaction(
                parsed_account=parsed,
                amount=amount,
                is_debit=(ttype == "debit"),
                raw_line=candidate,
            )
        )
    return transactions



