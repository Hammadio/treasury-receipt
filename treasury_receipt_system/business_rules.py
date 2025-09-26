"""Business rules engine for classifying transactions and applying rules."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional
import os

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuleOutcome:
    transaction_type: str  # "Interest" or "Principal Repayment" or "Unknown"
    additional_processing_required: bool
    reason: str


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
    def __init__(self, enable_llm: bool = True, llm: Optional[LocalLLMClassifier] = None) -> None:
        self.llm = (llm or LocalLLMClassifier()) if enable_llm else None

    @staticmethod
    def _heuristic_classify(gl_description: str) -> str:
        desc = gl_description.lower()
        if any(k in desc for k in ["interest", "coupon", "yield"]):
            return "Interest"
        if any(k in desc for k in ["principal", "loan repayment", "amortization", "capital repayment"]):
            return "Principal Repayment"
        return "Unknown"

    def classify_transaction(self, gl_account_description: str, amount: float) -> RuleOutcome:
        # First try LLM if available
        predicted: Optional[str] = None
        try:
            predicted = self.llm.classify(gl_account_description) if self.llm else None
        except Exception as exc:
            LOGGER.warning("Local LLM classification failed: %s", exc)

        label = predicted or self._heuristic_classify(gl_account_description)

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

    @staticmethod
    def apply_business_rules(transaction_type: str, amount: float) -> RuleOutcome:
        if transaction_type == "Interest":
            return RuleOutcome("Interest", False, "Interest receipt")
        if transaction_type == "Principal Repayment":
            return RuleOutcome("Principal Repayment", True, "Principal reduces assets")
        return RuleOutcome("Unknown", True, "Unknown type requires review")



