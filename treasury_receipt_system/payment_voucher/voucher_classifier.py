"""Payment Voucher classification logic."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Dict, List
import os

from .business_rules_config import BusinessRulesManager

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class VoucherClassification:
    """Classification result for Payment Voucher transactions."""
    category: str  # "Operating", "Capital", "Vendor", "Personnel", "Administrative"
    subcategory: str  # More specific classification
    approval_level: str  # "Standard", "High", "Executive"
    requires_approval: bool
    business_justification: str
    risk_level: str  # "Low", "Medium", "High"
    compliance_checks: List[str]  # List of required compliance checks


class PaymentVoucherClassifier:
    """Advanced classifier for Payment Voucher transactions."""
    
    def __init__(self, enable_llm: bool = True, llm_endpoint: Optional[str] = None, 
                 business_rules_file: Optional[str] = None):
        self.enable_llm = enable_llm
        self.llm_endpoint = llm_endpoint or os.getenv("LLM_ENDPOINT")
        
        # Load business rules from configuration
        self.business_rules = BusinessRulesManager(business_rules_file)
        
        # Legacy approval thresholds (now handled by business rules)
        self.approval_thresholds = {
            "Standard": 10000,    # Under $10K
            "High": 100000,       # $10K - $100K
            "Executive": float('inf')  # $100K+
        }
    
    def _get_approval_level_from_rules(self, amount: float, category: str) -> str:
        """Get approval level from business rules."""
        approval_rule = self.business_rules.get_approval_rule(amount, category)
        if approval_rule:
            return approval_rule.approval_level
        
        # Fallback to legacy thresholds
        if amount >= self.approval_thresholds["High"]:
            return "Executive"
        elif amount >= self.approval_thresholds["Standard"]:
            return "High"
        else:
            return "Standard"
    
    def classify_transaction(self, gl_description: str, amount: float, 
                           additional_context: Optional[Dict] = None) -> VoucherClassification:
        """Classify a transaction for Payment Voucher creation."""
        
        # Try LLM classification first if enabled
        if self.enable_llm and self.llm_endpoint:
            llm_result = self._llm_classify(gl_description, amount, additional_context)
            if llm_result:
                return llm_result
        
        # Use business rules for classification
        return self._classify_with_business_rules(gl_description, amount, additional_context)
    
    def _llm_classify(self, gl_description: str, amount: float, 
                     additional_context: Optional[Dict] = None) -> Optional[VoucherClassification]:
        """Use LLM for advanced classification."""
        try:
            import requests
            
            url = self.llm_endpoint.rstrip("/") + "/chat/completions"
            system_prompt = (
                "You are a Payment Voucher classification expert. "
                "Classify transactions into categories: Operating, Capital, Vendor, Personnel, Administrative. "
                "Provide subcategory, risk level, and required compliance checks. "
                "Consider amount thresholds for approval levels."
            )
            
            user_prompt = f"""
            GL Description: {gl_description}
            Amount: ${amount:,.2f}
            Additional Context: {additional_context or 'None'}
            
            Classify this transaction for Payment Voucher creation.
            """
            
            payload = {
                "model": os.getenv("LLM_MODEL", "Qwen3-8B-Instruct"),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 200
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            # Parse LLM response (simplified - would need more robust parsing)
            content = response.json()["choices"][0]["message"]["content"]
            return self._parse_llm_response(content, amount)
            
        except Exception as exc:
            LOGGER.warning("LLM classification failed: %s", exc)
            return None
    
    def _classify_with_business_rules(self, gl_description: str, amount: float, 
                                    additional_context: Optional[Dict] = None) -> VoucherClassification:
        """Classify using business rules configuration."""
        desc_lower = gl_description.lower()
        
        # Get all active classification rules
        rules = self.business_rules.get_classification_rules()
        
        # Find best matching rule
        best_rule = None
        best_score = 0
        
        for rule in rules:
            # Check if amount is within range
            amount_in_range = False
            for amount_range in rule.amount_ranges:
                if amount_range["min"] <= amount <= amount_range["max"]:
                    amount_in_range = True
                    break
            
            if not amount_in_range:
                continue
            
            # Calculate keyword match score
            score = 0
            for keyword in rule.keywords:
                if keyword.lower() in desc_lower:
                    score += 1
            
            # Weight by priority
            weighted_score = score * rule.priority
            
            if weighted_score > best_score:
                best_score = weighted_score
                best_rule = rule
        
        # If no rule matches, use default
        if not best_rule:
            best_rule = self._get_default_rule()
        
        # Get approval level from business rules
        approval_level = self._get_approval_level_from_rules(amount, best_rule.category)
        
        # Determine risk level based on category and amount
        risk_level = self._determine_risk_level(best_rule.category, amount)
        
        # Get compliance checks
        compliance_checks = self._get_compliance_checks(best_rule.category, amount)
        
        return VoucherClassification(
            category=best_rule.category,
            subcategory=best_rule.subcategory,
            approval_level=approval_level,
            requires_approval=approval_level != "Standard",
            business_justification=f"Classified as {best_rule.category} - {best_rule.subcategory}",
            risk_level=risk_level,
            compliance_checks=compliance_checks
        )
    
    def _get_default_rule(self):
        """Get default rule when no match is found."""
        from .business_rules_config import ClassificationRule
        return ClassificationRule(
            rule_id="DEFAULT",
            name="Default Classification",
            description="Default rule for unmatched transactions",
            keywords=[],
            gl_account_patterns=[],
            amount_ranges=[{"min": 0, "max": 1000000}],
            category="Administrative",
            subcategory="General Administrative",
            priority=1,
            is_active=True,
            created_by="System",
            created_date="",
            last_modified=""
        )
    
    def _determine_risk_level(self, category: str, amount: float) -> str:
        """Determine risk level based on category and amount."""
        # Base risk by category
        category_risk = {
            "Operating": "Low",
            "Administrative": "Low", 
            "Capital": "Medium",
            "Vendor": "Medium",
            "Personnel": "High"
        }
        
        base_risk = category_risk.get(category, "Medium")
        
        # Adjust for amount
        if amount >= 100000:
            return "High"
        elif amount >= 50000:
            return "Medium" if base_risk == "Low" else "High"
        else:
            return base_risk
    
    def _get_compliance_checks(self, category: str, amount: float) -> List[str]:
        """Get required compliance checks based on category and amount."""
        checks = ["budget_approval"]
        
        if category == "Capital":
            checks.extend(["asset_approval", "depreciation_setup"])
        elif category == "Vendor":
            checks.extend(["vendor_verification", "contract_validation"])
        elif category == "Personnel":
            checks.extend(["hr_approval", "payroll_validation"])
        
        if amount >= 50000:
            checks.append("high_value_approval")
        
        return checks
    
    def _parse_llm_response(self, content: str, amount: float) -> VoucherClassification:
        """Parse LLM response into VoucherClassification."""
        # Simplified parsing - would need more robust implementation
        content_lower = content.lower()
        
        category = "Administrative"  # Default
        if "operating" in content_lower:
            category = "Operating"
        elif "capital" in content_lower:
            category = "Capital"
        elif "vendor" in content_lower:
            category = "Vendor"
        elif "personnel" in content_lower:
            category = "Personnel"
        
        approval_level = self._determine_approval_level(amount)
        risk_level = "Medium"  # Default
        if "low" in content_lower:
            risk_level = "Low"
        elif "high" in content_lower:
            risk_level = "High"
        
        return VoucherClassification(
            category=category,
            subcategory="General",
            approval_level=approval_level,
            requires_approval=approval_level != "Standard",
            business_justification="LLM classified",
            risk_level=risk_level,
            compliance_checks=["budget_approval"]
        )
    
    def _heuristic_classify(self, gl_description: str, amount: float, 
                           additional_context: Optional[Dict] = None) -> VoucherClassification:
        """Heuristic classification based on keywords and rules."""
        desc_lower = gl_description.lower()
        
        # Find best matching category
        best_category = "Administrative"
        best_score = 0
        subcategory = "General"
        
        for category, rules in self.classification_rules.items():
            score = sum(1 for keyword in rules["keywords"] if keyword in desc_lower)
            if score > best_score:
                best_score = score
                best_category = category
                
                # Find subcategory
                for subcat, subcat_keywords in rules["subcategories"].items():
                    if any(keyword in desc_lower for keyword in subcat_keywords):
                        subcategory = subcat
                        break
        
        # Get category rules
        category_rules = self.classification_rules[best_category]
        
        # Determine approval level
        approval_level = self._determine_approval_level(amount)
        
        # Build compliance checks
        compliance_checks = category_rules["compliance_checks"].copy()
        if amount >= 50000:  # High-value transactions need additional checks
            compliance_checks.append("high_value_approval")
        
        return VoucherClassification(
            category=best_category,
            subcategory=subcategory,
            approval_level=approval_level,
            requires_approval=approval_level != "Standard",
            business_justification=f"Classified as {best_category} - {subcategory}",
            risk_level=category_rules["risk_level"],
            compliance_checks=compliance_checks
        )
    
    def _determine_approval_level(self, amount: float) -> str:
        """Determine approval level based on amount thresholds."""
        if amount >= self.approval_thresholds["High"]:
            return "Executive"
        elif amount >= self.approval_thresholds["Standard"]:
            return "High"
        else:
            return "Standard"
    
    def get_approval_workflow(self, classification: VoucherClassification) -> List[str]:
        """Get the approval workflow steps for a classification."""
        workflows = {
            "Standard": ["Department Head Approval"],
            "High": ["Department Head Approval", "Finance Director Approval"],
            "Executive": ["Department Head Approval", "Finance Director Approval", "Executive Approval"]
        }
        return workflows.get(classification.approval_level, ["Manual Review Required"])
