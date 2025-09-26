"""Account parsing and validation logic."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .utils import ParsedAccount, Transaction, parse_transaction_lines
from .reference_lookup import ReferenceLookup

LOGGER = logging.getLogger(__name__)


@dataclass
class AccountDescriptions:
    entity: str
    cost_center: str
    gl_account: str
    budget_group: str
    future1: str
    future2: str
    future3: str


class AccountParser:
    """Parse and validate accounts against reference data."""

    def __init__(self, reference: ReferenceLookup) -> None:
        self.reference = reference

    def parse_text_transactions(self, text: str) -> List[Transaction]:
        return parse_transaction_lines(text)

    def validate_account(self, parsed: ParsedAccount) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        if not self.reference.get_entity_description(parsed.entity):
            errors.append(f"Unknown Entity: {parsed.entity}")
        if not self.reference.get_cost_center_description(parsed.cost_center):
            errors.append(f"Unknown Cost Center: {parsed.cost_center}")
        if not self.reference.get_gl_account_description(parsed.gl_account):
            errors.append(f"Unknown GL Account: {parsed.gl_account}")
        if not self.reference.get_budget_group_description(parsed.budget_group):
            errors.append(f"Unknown Budget Group: {parsed.budget_group}")
        # Futures are optional but if present in lookup, validate; otherwise fall back to generic futures lookup
        for idx, future_code in enumerate([parsed.future1, parsed.future2, parsed.future3], start=1):
            if self.reference.get_futures_description(future_code) is None:
                # Not found; not necessarily an error if the Futures sheet is incomplete, but flag
                LOGGER.debug("Future%d code not found in lookup: %s", idx, future_code)
        return (len(errors) == 0, errors)

    def lookup_descriptions(self, parsed: ParsedAccount) -> AccountDescriptions:
        return AccountDescriptions(
            entity=self.reference.get_entity_description(parsed.entity) or parsed.entity,
            cost_center=self.reference.get_cost_center_description(parsed.cost_center) or parsed.cost_center,
            gl_account=self.reference.get_gl_account_description(parsed.gl_account) or parsed.gl_account,
            budget_group=self.reference.get_budget_group_description(parsed.budget_group) or parsed.budget_group,
            future1=self.reference.get_futures_description(parsed.future1) or parsed.future1,
            future2=self.reference.get_futures_description(parsed.future2) or parsed.future2,
            future3=self.reference.get_futures_description(parsed.future3) or parsed.future3,
        )



