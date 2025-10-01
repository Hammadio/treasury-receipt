"""Business rules engine for classifying transactions and applying rules."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional
import os

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuleOutcome:
    transaction_type: str  # "Interest" or "Principal Repayment" or "Unknown" for TR; "Operating Expense", "Capital Expenditure", etc. for PV
    additional_processing_required: bool
    reason: str
    approval_level: str = "Standard"  # "Standard", "High", "Executive" for Payment Vouchers
    voucher_category: str = ""  # For Payment Vouchers: "Operating", "Capital", "Vendor", etc.


class LocalLLMClassifier:
    """Optional hook to use a local LLM (e.g., Qwen) for classification.

    Implement the `classify` method to call your on-prem LLM endpoint.
    If not configured, return None to fall back to heuristics.
    """

    def __init__(self, endpoint: Optional[str] = None, model: Optional[str] = None) -> None:
        # Configure via args or environment variables
        # Expected OpenAI-compatible server (e.g., vLLM, Ollama /openai, TGI wrapper)
        self.endpoint = endpoint or os.getenv("LLM_ENDPOINT")  # e.g., http://localhost:8000/v1
        self.model = model or os.getenv("LLM_MODEL", "Qwen3-8B-Instruct")
        self.api_key = os.getenv("LLM_API_KEY", "sk-local")  # not required for most local servers

    def classify(self, text: str) -> Optional[str]:
        """Classify using a local OpenAI-compatible endpoint if configured.

        Returns one of: "Interest", "Principal Repayment" or None if unavailable.
        """
        if not self.endpoint:
            return None
        # Lazy import to avoid hard dependency if LLM is disabled
        try:
            import requests  # type: ignore
        except Exception:
            return None
        url = self.endpoint.rstrip("/") + "/chat/completions"
        system_prompt = (
            "You are a strict classifier for public finance transactions. "
            "Given a GL account description, reply with exactly one label: "
            "Interest or Principal Repayment. If unclear, reply Unknown."
        )
        user_prompt = f"GL Account Description: {text}"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 5,
        }
        headers = {"Content-Type": "application/json"}
        # Many local servers ignore Authorization, but include if provided
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            # Normalize simple outputs
            content_lower = content.lower()
            if "interest" in content_lower:
                return "Interest"
            if "principal" in content_lower:
                return "Principal Repayment"
            if "unknown" in content_lower:
                return "Unknown"
            return None
        except Exception as exc:
            LOGGER.debug("Local LLM call failed: %s", exc)
            return None


class BusinessRules:
    def __init__(self, enable_llm: bool = True, llm: Optional[LocalLLMClassifier] = None, system_mode: str = "treasury_receipt") -> None:
        self.llm = (llm or LocalLLMClassifier()) if enable_llm else None
        self.system_mode = system_mode  # "treasury_receipt" or "payment_voucher"

    @staticmethod
    def _heuristic_classify_treasury_receipt(gl_description: str) -> str:
        desc = gl_description.lower()
        if any(k in desc for k in ["interest", "coupon", "yield"]):
            return "Interest"
        if any(k in desc for k in ["principal", "loan repayment", "amortization", "capital repayment"]):
            return "Principal Repayment"
        return "Unknown"

    @staticmethod
    def _heuristic_classify_payment_voucher(gl_description: str) -> str:
        desc = gl_description.lower()
        # Operating Expenses
        if any(k in desc for k in ["office supplies", "utilities", "telecommunications", "travel", "training", "consulting", "maintenance"]):
            return "Operating Expense"
        # Capital Expenditures
        if any(k in desc for k in ["equipment", "furniture", "software", "hardware", "infrastructure", "construction"]):
            return "Capital Expenditure"
        # Vendor Payments
        if any(k in desc for k in ["vendor", "supplier", "contractor", "service provider", "professional services"]):
            return "Vendor Payment"
        # Personnel Costs
        if any(k in desc for k in ["salary", "wages", "benefits", "payroll", "compensation"]):
            return "Personnel Cost"
        # Administrative
        if any(k in desc for k in ["administrative", "general", "overhead", "management"]):
            return "Administrative Expense"
        return "Unknown"

    def _heuristic_classify(self, gl_description: str) -> str:
        if self.system_mode == "payment_voucher":
            return self._heuristic_classify_payment_voucher(gl_description)
        else:
            return self._heuristic_classify_treasury_receipt(gl_description)

    def classify_transaction(self, gl_account_description: str, amount: float) -> RuleOutcome:
        # First try LLM if available
        predicted: Optional[str] = None
        try:
            predicted = self.llm.classify(gl_account_description) if self.llm else None
        except Exception as exc:
            LOGGER.warning("Local LLM classification failed: %s", exc)

        label = predicted or self._heuristic_classify(gl_account_description)

        if self.system_mode == "payment_voucher":
            return self._classify_payment_voucher(label, amount)
        else:
            return self._classify_treasury_receipt(label)

    def _classify_treasury_receipt(self, label: str) -> RuleOutcome:
        if label == "Interest":
            return RuleOutcome(
                transaction_type="Interest",
                additional_processing_required=False,
                reason="Interest receipts are final; direct TR creation",
            )
        if label == "Principal Repayment":
            return RuleOutcome(
                transaction_type="Principal Repayment",
                additional_processing_required=True,
                reason="Principal reduces asset balance; reflect on assets side",
            )
        return RuleOutcome(
            transaction_type="Unknown",
            additional_processing_required=True,
            reason="Unclear classification; flag for manual review",
        )

    def _classify_payment_voucher(self, label: str, amount: float) -> RuleOutcome:
        # Determine approval level based on amount
        approval_level = self._determine_approval_level(amount)
        
        if label == "Operating Expense":
            return RuleOutcome(
                transaction_type="Operating Expense",
                additional_processing_required=False,
                reason="Standard operating expense; direct PV creation",
                approval_level=approval_level,
                voucher_category="Operating"
            )
        elif label == "Capital Expenditure":
            return RuleOutcome(
                transaction_type="Capital Expenditure",
                additional_processing_required=True,
                reason="Capital expenditure requires asset tracking and depreciation setup",
                approval_level=approval_level,
                voucher_category="Capital"
            )
        elif label == "Vendor Payment":
            return RuleOutcome(
                transaction_type="Vendor Payment",
                additional_processing_required=True,
                reason="Vendor payment requires vendor verification and contract validation",
                approval_level=approval_level,
                voucher_category="Vendor"
            )
        elif label == "Personnel Cost":
            return RuleOutcome(
                transaction_type="Personnel Cost",
                additional_processing_required=True,
                reason="Personnel costs require HR validation and payroll integration",
                approval_level=approval_level,
                voucher_category="Personnel"
            )
        elif label == "Administrative Expense":
            return RuleOutcome(
                transaction_type="Administrative Expense",
                additional_processing_required=False,
                reason="Standard administrative expense; direct PV creation",
                approval_level=approval_level,
                voucher_category="Administrative"
            )
        else:
            return RuleOutcome(
                transaction_type="Unknown",
                additional_processing_required=True,
                reason="Unclear classification; flag for manual review",
                approval_level="Executive",
                voucher_category="Unknown"
            )

    def _determine_approval_level(self, amount: float) -> str:
        """Determine approval level based on amount thresholds."""
        if amount >= 100000:  # $100K+
            return "Executive"
        elif amount >= 10000:  # $10K-$100K
            return "High"
        else:  # Under $10K
            return "Standard"

    @staticmethod
    def apply_business_rules(transaction_type: str, amount: float) -> RuleOutcome:
        if transaction_type == "Interest":
            return RuleOutcome("Interest", False, "Interest receipt")
        if transaction_type == "Principal Repayment":
            return RuleOutcome("Principal Repayment", True, "Principal reduces assets")
        return RuleOutcome("Unknown", True, "Unknown type requires review")



