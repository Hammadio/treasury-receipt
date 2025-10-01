"""
Business Rules Configuration for Payment Voucher Creation Agent.

This module contains all business rules that can be easily modified by business users
without requiring code changes. Rules are organized by category and can be updated
through configuration files or a web interface.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path

LOGGER = logging.getLogger(__name__)


@dataclass
class ClassificationRule:
    """Individual classification rule."""
    rule_id: str
    name: str
    description: str
    keywords: List[str]
    gl_account_patterns: List[str]  # e.g., ["6*", "601*", "602*"]
    amount_ranges: List[Dict[str, float]]  # [{"min": 0, "max": 10000}]
    category: str
    subcategory: str
    priority: int  # Higher number = higher priority
    is_active: bool = True
    created_by: str = "System"
    created_date: str = ""
    last_modified: str = ""


@dataclass
class ApprovalRule:
    """Approval workflow rule."""
    rule_id: str
    name: str
    description: str
    conditions: Dict[str, Any]  # Amount ranges, categories, etc.
    approval_level: str  # "Standard", "High", "Executive"
    required_approvers: List[str]
    escalation_rules: Dict[str, Any]
    is_active: bool = True


@dataclass
class ValidationRule:
    """Validation rule for vouchers."""
    rule_id: str
    name: str
    description: str
    rule_type: str  # "amount", "gl_account", "category", "compliance"
    conditions: Dict[str, Any]
    error_message: str
    warning_message: str = ""
    is_active: bool = True


@dataclass
class BusinessRulesConfig:
    """Complete business rules configuration."""
    version: str
    last_updated: str
    classification_rules: List[ClassificationRule]
    approval_rules: List[ApprovalRule]
    validation_rules: List[ValidationRule]
    global_settings: Dict[str, Any]


class BusinessRulesManager:
    """Manages business rules configuration and updates."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "business_rules.json"
        self.config = self._load_default_config()
        self._load_from_file()
    
    def _load_default_config(self) -> BusinessRulesConfig:
        """Load default business rules configuration."""
        return BusinessRulesConfig(
            version="1.0.0",
            last_updated=datetime.now().isoformat(),
            classification_rules=self._get_default_classification_rules(),
            approval_rules=self._get_default_approval_rules(),
            validation_rules=self._get_default_validation_rules(),
            global_settings=self._get_default_global_settings()
        )
    
    def _get_default_classification_rules(self) -> List[ClassificationRule]:
        """Get default classification rules."""
        return [
            # Operating Expenses
            ClassificationRule(
                rule_id="OP-001",
                name="Office Supplies",
                description="Office supplies and stationery",
                keywords=["office supplies", "stationery", "pens", "paper", "notebooks", "staplers"],
                gl_account_patterns=["6*", "601*", "602*"],
                amount_ranges=[{"min": 0, "max": 1000000}],
                category="Operating",
                subcategory="Office Supplies",
                priority=100,
                created_by="System",
                created_date=datetime.now().isoformat(),
                last_modified=datetime.now().isoformat()
            ),
            ClassificationRule(
                rule_id="OP-002",
                name="Utilities",
                description="Utility payments",
                keywords=["utilities", "electricity", "water", "gas", "internet", "phone", "telecommunications"],
                gl_account_patterns=["6*", "603*"],
                amount_ranges=[{"min": 0, "max": 1000000}],
                category="Operating",
                subcategory="Utilities",
                priority=100,
                created_by="System",
                created_date=datetime.now().isoformat(),
                last_modified=datetime.now().isoformat()
            ),
            ClassificationRule(
                rule_id="OP-003",
                name="Travel Expenses",
                description="Business travel and transportation",
                keywords=["travel", "transportation", "accommodation", "meals", "hotel", "flight", "taxi"],
                gl_account_patterns=["6*", "604*"],
                amount_ranges=[{"min": 0, "max": 1000000}],
                category="Operating",
                subcategory="Travel",
                priority=100,
                created_by="System",
                created_date=datetime.now().isoformat(),
                last_modified=datetime.now().isoformat()
            ),
            
            # Capital Expenditures
            ClassificationRule(
                rule_id="CAP-001",
                name="IT Equipment",
                description="Computer and IT equipment",
                keywords=["computer", "laptop", "desktop", "server", "software", "hardware", "printer", "monitor"],
                gl_account_patterns=["1*", "11*", "12*"],
                amount_ranges=[{"min": 0, "max": 1000000}],
                category="Capital",
                subcategory="IT Equipment",
                priority=100,
                created_by="System",
                created_date=datetime.now().isoformat(),
                last_modified=datetime.now().isoformat()
            ),
            ClassificationRule(
                rule_id="CAP-002",
                name="Office Furniture",
                description="Office furniture and fixtures",
                keywords=["furniture", "desk", "chair", "cabinet", "shelf", "table", "filing cabinet"],
                gl_account_patterns=["1*", "13*"],
                amount_ranges=[{"min": 0, "max": 1000000}],
                category="Capital",
                subcategory="Office Furniture",
                priority=100,
                created_by="System",
                created_date=datetime.now().isoformat(),
                last_modified=datetime.now().isoformat()
            ),
            
            # Vendor Payments
            ClassificationRule(
                rule_id="VEN-001",
                name="Service Providers",
                description="External service providers and contractors",
                keywords=["vendor", "supplier", "contractor", "service provider", "consultant", "outsourcing"],
                gl_account_patterns=["6*", "2*"],
                amount_ranges=[{"min": 0, "max": 1000000}],
                category="Vendor",
                subcategory="Service Provider",
                priority=100,
                created_by="System",
                created_date=datetime.now().isoformat(),
                last_modified=datetime.now().isoformat()
            ),
            
            # Personnel Costs
            ClassificationRule(
                rule_id="PER-001",
                name="Employee Compensation",
                description="Employee salaries and benefits",
                keywords=["salary", "wages", "compensation", "benefits", "payroll", "bonus", "incentive"],
                gl_account_patterns=["6*", "61*"],
                amount_ranges=[{"min": 0, "max": 1000000}],
                category="Personnel",
                subcategory="Employee Compensation",
                priority=100,
                created_by="System",
                created_date=datetime.now().isoformat(),
                last_modified=datetime.now().isoformat()
            ),
            
            # Administrative
            ClassificationRule(
                rule_id="ADM-001",
                name="General Administrative",
                description="General administrative expenses",
                keywords=["administrative", "general", "overhead", "management", "governance"],
                gl_account_patterns=["6*", "69*"],
                amount_ranges=[{"min": 0, "max": 1000000}],
                category="Administrative",
                subcategory="General Administrative",
                priority=50,  # Lower priority - catch-all
                created_by="System",
                created_date=datetime.now().isoformat(),
                last_modified=datetime.now().isoformat()
            )
        ]
    
    def _get_default_approval_rules(self) -> List[ApprovalRule]:
        """Get default approval rules."""
        return [
            ApprovalRule(
                rule_id="APP-001",
                name="Standard Approval",
                description="Standard approval for amounts under $10,000",
                conditions={"max_amount": 10000, "categories": ["Operating", "Administrative"]},
                approval_level="Standard",
                required_approvers=["Department Head", "Finance Processor"],
                escalation_rules={"timeout_hours": 48, "escalate_to": "Finance Director"},
                is_active=True
            ),
            ApprovalRule(
                rule_id="APP-002",
                name="High Value Approval",
                description="High approval for amounts $10,000 - $100,000",
                conditions={"min_amount": 10000, "max_amount": 100000},
                approval_level="High",
                required_approvers=["Department Head", "Finance Director", "Finance Processor"],
                escalation_rules={"timeout_hours": 72, "escalate_to": "Executive"},
                is_active=True
            ),
            ApprovalRule(
                rule_id="APP-003",
                name="Executive Approval",
                description="Executive approval for amounts over $100,000",
                conditions={"min_amount": 100000},
                approval_level="Executive",
                required_approvers=["Department Head", "Finance Director", "Executive", "Finance Processor"],
                escalation_rules={"timeout_hours": 96, "escalate_to": "CEO"},
                is_active=True
            ),
            ApprovalRule(
                rule_id="APP-004",
                name="Capital Expenditure Approval",
                description="Special approval for capital expenditures",
                conditions={"categories": ["Capital"], "min_amount": 5000},
                approval_level="High",
                required_approvers=["Department Head", "Asset Manager", "Finance Director", "Finance Processor"],
                escalation_rules={"timeout_hours": 72, "escalate_to": "Executive"},
                is_active=True
            ),
            ApprovalRule(
                rule_id="APP-005",
                name="Vendor Payment Approval",
                description="Special approval for vendor payments",
                conditions={"categories": ["Vendor"], "min_amount": 10000},
                approval_level="High",
                required_approvers=["Department Head", "Procurement Manager", "Finance Director", "Finance Processor"],
                escalation_rules={"timeout_hours": 72, "escalate_to": "Executive"},
                is_active=True
            )
        ]
    
    def _get_default_validation_rules(self) -> List[ValidationRule]:
        """Get default validation rules."""
        return [
            ValidationRule(
                rule_id="VAL-001",
                name="Amount Validation",
                description="Validate amount is positive and within limits",
                rule_type="amount",
                conditions={"min_amount": 0.01, "max_amount": 10000000},
                error_message="Amount must be between $0.01 and $10,000,000",
                is_active=True
            ),
            ValidationRule(
                rule_id="VAL-002",
                name="GL Account Category Match",
                description="Validate GL account matches transaction category",
                rule_type="gl_account",
                conditions={
                    "Operating": ["6*"],
                    "Capital": ["1*"],
                    "Vendor": ["6*", "2*"],
                    "Personnel": ["6*"],
                    "Administrative": ["6*"]
                },
                error_message="GL account does not match transaction category",
                warning_message="GL account category mismatch - please verify",
                is_active=True
            ),
            ValidationRule(
                rule_id="VAL-003",
                name="High Amount Documentation",
                description="Require additional documentation for high amounts",
                rule_type="compliance",
                conditions={"min_amount": 50000},
                error_message="",
                warning_message="High amount transaction - additional documentation required",
                is_active=True
            ),
            ValidationRule(
                rule_id="VAL-004",
                name="Capital Expenditure Validation",
                description="Validate capital expenditure requirements",
                rule_type="category",
                conditions={"category": "Capital", "min_amount": 1000},
                error_message="Capital expenditures require asset approval and depreciation setup",
                warning_message="Ensure asset tracking is configured",
                is_active=True
            )
        ]
    
    def _get_default_global_settings(self) -> Dict[str, Any]:
        """Get default global settings."""
        return {
            "default_currency": "USD",
            "default_department": "Finance",
            "voucher_number_prefix": "PV",
            "approval_timeout_hours": 72,
            "max_retry_attempts": 3,
            "enable_llm_classification": True,
            "enable_auto_approval": False,
            "require_business_justification": True,
            "enable_duplicate_check": True,
            "duplicate_check_days": 30
        }
    
    def _load_from_file(self):
        """Load configuration from file if it exists."""
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert dict back to dataclass objects
                    self.config = self._dict_to_config(data)
                LOGGER.info(f"Loaded business rules from {self.config_file}")
        except Exception as e:
            LOGGER.warning(f"Could not load business rules from file: {e}")
    
    def save_to_file(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config_to_dict(), f, indent=2, ensure_ascii=False)
            LOGGER.info(f"Saved business rules to {self.config_file}")
        except Exception as e:
            LOGGER.error(f"Could not save business rules to file: {e}")
    
    def _config_to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for JSON serialization."""
        return {
            "version": self.config.version,
            "last_updated": self.config.last_updated,
            "classification_rules": [asdict(rule) for rule in self.config.classification_rules],
            "approval_rules": [asdict(rule) for rule in self.config.approval_rules],
            "validation_rules": [asdict(rule) for rule in self.config.validation_rules],
            "global_settings": self.config.global_settings
        }
    
    def _dict_to_config(self, data: Dict[str, Any]) -> BusinessRulesConfig:
        """Convert dictionary back to config object."""
        return BusinessRulesConfig(
            version=data.get("version", "1.0.0"),
            last_updated=data.get("last_updated", datetime.now().isoformat()),
            classification_rules=[ClassificationRule(**rule) for rule in data.get("classification_rules", [])],
            approval_rules=[ApprovalRule(**rule) for rule in data.get("approval_rules", [])],
            validation_rules=[ValidationRule(**rule) for rule in data.get("validation_rules", [])],
            global_settings=data.get("global_settings", {})
        )
    
    def add_classification_rule(self, rule: ClassificationRule):
        """Add a new classification rule."""
        rule.created_date = datetime.now().isoformat()
        rule.last_modified = datetime.now().isoformat()
        self.config.classification_rules.append(rule)
        self.config.last_updated = datetime.now().isoformat()
        LOGGER.info(f"Added classification rule: {rule.rule_id}")
    
    def update_classification_rule(self, rule_id: str, updates: Dict[str, Any]):
        """Update an existing classification rule."""
        for rule in self.config.classification_rules:
            if rule.rule_id == rule_id:
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                rule.last_modified = datetime.now().isoformat()
                self.config.last_updated = datetime.now().isoformat()
                LOGGER.info(f"Updated classification rule: {rule_id}")
                return True
        return False
    
    def get_classification_rules(self, category: Optional[str] = None) -> List[ClassificationRule]:
        """Get classification rules, optionally filtered by category."""
        rules = [rule for rule in self.config.classification_rules if rule.is_active]
        if category:
            rules = [rule for rule in rules if rule.category == category]
        return sorted(rules, key=lambda x: x.priority, reverse=True)
    
    def get_approval_rule(self, amount: float, category: str) -> Optional[ApprovalRule]:
        """Get the appropriate approval rule for given amount and category."""
        for rule in self.config.approval_rules:
            if not rule.is_active:
                continue
            
            conditions = rule.conditions
            amount_match = True
            category_match = True
            
            if "min_amount" in conditions and amount < conditions["min_amount"]:
                amount_match = False
            if "max_amount" in conditions and amount > conditions["max_amount"]:
                amount_match = False
            if "categories" in conditions and category not in conditions["categories"]:
                category_match = False
            
            if amount_match and category_match:
                return rule
        
        return None
    
    def get_validation_rules(self, rule_type: Optional[str] = None) -> List[ValidationRule]:
        """Get validation rules, optionally filtered by type."""
        rules = [rule for rule in self.config.validation_rules if rule.is_active]
        if rule_type:
            rules = [rule for rule in rules if rule.rule_type == rule_type]
        return rules
    
    def export_rules(self, file_path: str):
        """Export rules to a file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self._config_to_dict(), f, indent=2, ensure_ascii=False)
        LOGGER.info(f"Exported business rules to {file_path}")
    
    def import_rules(self, file_path: str):
        """Import rules from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.config = self._dict_to_config(data)
            LOGGER.info(f"Imported business rules from {file_path}")
        except Exception as e:
            LOGGER.error(f"Could not import business rules from file: {e}")
    
    def validate_rules(self) -> List[str]:
        """Validate all rules for consistency and errors."""
        errors = []
        
        # Check for duplicate rule IDs
        classification_ids = [rule.rule_id for rule in self.config.classification_rules]
        if len(classification_ids) != len(set(classification_ids)):
            errors.append("Duplicate classification rule IDs found")
        
        # Check for missing required fields
        for rule in self.config.classification_rules:
            if not rule.keywords:
                errors.append(f"Classification rule {rule.rule_id} has no keywords")
            if not rule.gl_account_patterns:
                errors.append(f"Classification rule {rule.rule_id} has no GL account patterns")
        
        return errors
