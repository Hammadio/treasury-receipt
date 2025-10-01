#!/usr/bin/env python3
"""
Business Rules Editor for Payment Voucher Creation Agent.

This tool allows business users to easily add, modify, and manage business rules
without requiring technical knowledge or code changes.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the treasury_receipt_system to the path
sys.path.insert(0, str(Path(__file__).parent / "treasury_receipt_system"))

from treasury_receipt_system.payment_voucher.business_rules_config import (
    BusinessRulesManager, ClassificationRule, ApprovalRule, ValidationRule
)


class BusinessRulesEditor:
    """Interactive editor for business rules."""
    
    def __init__(self, config_file: str = "business_rules.json"):
        self.manager = BusinessRulesManager(config_file)
        self.config_file = config_file
    
    def show_main_menu(self):
        """Display the main menu."""
        print("\n" + "="*60)
        print("PAYMENT VOUCHER BUSINESS RULES EDITOR")
        print("="*60)
        print("1. View Current Rules")
        print("2. Add Classification Rule")
        print("3. Modify Classification Rule")
        print("4. Add Approval Rule")
        print("5. Add Validation Rule")
        print("6. Test Rules")
        print("7. Export Rules")
        print("8. Import Rules")
        print("9. Validate Rules")
        print("0. Exit")
        print("="*60)
    
    def view_rules(self):
        """Display current rules."""
        print("\n" + "="*60)
        print("CURRENT BUSINESS RULES")
        print("="*60)
        
        # Classification Rules
        print(f"\n📋 CLASSIFICATION RULES ({len(self.manager.config.classification_rules)})")
        print("-" * 40)
        for rule in self.manager.config.classification_rules:
            status = "✅" if rule.is_active else "❌"
            print(f"{status} {rule.rule_id}: {rule.name}")
            print(f"   Category: {rule.category} | Subcategory: {rule.subcategory}")
            print(f"   Keywords: {', '.join(rule.keywords[:3])}{'...' if len(rule.keywords) > 3 else ''}")
            print(f"   GL Patterns: {', '.join(rule.gl_account_patterns)}")
            print()
        
        # Approval Rules
        print(f"\n✅ APPROVAL RULES ({len(self.manager.config.approval_rules)})")
        print("-" * 40)
        for rule in self.manager.config.approval_rules:
            status = "✅" if rule.is_active else "❌"
            print(f"{status} {rule.rule_id}: {rule.name}")
            print(f"   Level: {rule.approval_level}")
            print(f"   Approvers: {', '.join(rule.required_approvers)}")
            print()
        
        # Validation Rules
        print(f"\n🔍 VALIDATION RULES ({len(self.manager.config.validation_rules)})")
        print("-" * 40)
        for rule in self.manager.config.validation_rules:
            status = "✅" if rule.is_active else "❌"
            print(f"{status} {rule.rule_id}: {rule.name}")
            print(f"   Type: {rule.rule_type}")
            print(f"   Error: {rule.error_message}")
            print()
    
    def add_classification_rule(self):
        """Add a new classification rule."""
        print("\n" + "="*60)
        print("ADD NEW CLASSIFICATION RULE")
        print("="*60)
        
        rule_id = input("Rule ID (e.g., OP-003): ").strip()
        if not rule_id:
            print("❌ Rule ID is required")
            return
        
        # Check if rule ID already exists
        existing_ids = [rule.rule_id for rule in self.manager.config.classification_rules]
        if rule_id in existing_ids:
            print(f"❌ Rule ID {rule_id} already exists")
            return
        
        name = input("Rule Name (e.g., Office Supplies): ").strip()
        description = input("Description: ").strip()
        
        print("\nKeywords (comma-separated):")
        keywords_input = input("e.g., office supplies, stationery, pens: ").strip()
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
        
        print("\nGL Account Patterns (comma-separated):")
        gl_patterns_input = input("e.g., 6*, 601*, 602*: ").strip()
        gl_patterns = [p.strip() for p in gl_patterns_input.split(",") if p.strip()]
        
        print("\nCategory:")
        print("1. Operating")
        print("2. Capital")
        print("3. Vendor")
        print("4. Personnel")
        print("5. Administrative")
        category_choice = input("Choose (1-5): ").strip()
        category_map = {
            "1": "Operating", "2": "Capital", "3": "Vendor", 
            "4": "Personnel", "5": "Administrative"
        }
        category = category_map.get(category_choice, "Operating")
        
        subcategory = input("Subcategory (e.g., Office Supplies): ").strip()
        
        try:
            priority = int(input("Priority (higher = more important, default 100): ").strip() or "100")
        except ValueError:
            priority = 100
        
        # Amount ranges
        print("\nAmount Ranges (press Enter for default 0-1000000):")
        min_amount = input("Minimum amount (default 0): ").strip()
        max_amount = input("Maximum amount (default 1000000): ").strip()
        
        try:
            min_val = float(min_amount) if min_amount else 0
            max_val = float(max_amount) if max_amount else 1000000
            amount_ranges = [{"min": min_val, "max": max_val}]
        except ValueError:
            amount_ranges = [{"min": 0, "max": 1000000}]
        
        # Create the rule
        rule = ClassificationRule(
            rule_id=rule_id,
            name=name,
            description=description,
            keywords=keywords,
            gl_account_patterns=gl_patterns,
            amount_ranges=amount_ranges,
            category=category,
            subcategory=subcategory,
            priority=priority,
            is_active=True,
            created_by="Business User",
            created_date="",
            last_modified=""
        )
        
        # Add the rule
        self.manager.add_classification_rule(rule)
        self.manager.save_to_file()
        
        print(f"\n✅ Successfully added classification rule: {rule_id}")
    
    def modify_classification_rule(self):
        """Modify an existing classification rule."""
        print("\n" + "="*60)
        print("MODIFY CLASSIFICATION RULE")
        print("="*60)
        
        # Show existing rules
        print("Existing Classification Rules:")
        for i, rule in enumerate(self.manager.config.classification_rules, 1):
            print(f"{i}. {rule.rule_id}: {rule.name} ({rule.category})")
        
        try:
            choice = int(input("\nSelect rule to modify (number): ").strip())
            if 1 <= choice <= len(self.manager.config.classification_rules):
                rule = self.manager.config.classification_rules[choice - 1]
                print(f"\nModifying rule: {rule.rule_id} - {rule.name}")
                
                # Show modification options
                print("\nWhat would you like to modify?")
                print("1. Keywords")
                print("2. GL Account Patterns")
                print("3. Category/Subcategory")
                print("4. Priority")
                print("5. Amount Ranges")
                print("6. Activate/Deactivate")
                
                mod_choice = input("Choose (1-6): ").strip()
                
                updates = {}
                
                if mod_choice == "1":
                    keywords_input = input(f"New keywords (current: {', '.join(rule.keywords)}): ").strip()
                    if keywords_input:
                        updates["keywords"] = [k.strip() for k in keywords_input.split(",") if k.strip()]
                
                elif mod_choice == "2":
                    gl_input = input(f"New GL patterns (current: {', '.join(rule.gl_account_patterns)}): ").strip()
                    if gl_input:
                        updates["gl_account_patterns"] = [p.strip() for p in gl_input.split(",") if p.strip()]
                
                elif mod_choice == "3":
                    print("Categories: Operating, Capital, Vendor, Personnel, Administrative")
                    new_category = input(f"New category (current: {rule.category}): ").strip()
                    if new_category:
                        updates["category"] = new_category
                    
                    new_subcategory = input(f"New subcategory (current: {rule.subcategory}): ").strip()
                    if new_subcategory:
                        updates["subcategory"] = new_subcategory
                
                elif mod_choice == "4":
                    new_priority = input(f"New priority (current: {rule.priority}): ").strip()
                    if new_priority:
                        try:
                            updates["priority"] = int(new_priority)
                        except ValueError:
                            print("❌ Invalid priority value")
                
                elif mod_choice == "5":
                    print("Amount Ranges:")
                    min_amount = input(f"New minimum (current: {rule.amount_ranges[0]['min']}): ").strip()
                    max_amount = input(f"New maximum (current: {rule.amount_ranges[0]['max']}): ").strip()
                    
                    try:
                        min_val = float(min_amount) if min_amount else rule.amount_ranges[0]['min']
                        max_val = float(max_amount) if max_amount else rule.amount_ranges[0]['max']
                        updates["amount_ranges"] = [{"min": min_val, "max": max_val}]
                    except ValueError:
                        print("❌ Invalid amount values")
                
                elif mod_choice == "6":
                    new_status = input(f"Activate rule? (current: {'Active' if rule.is_active else 'Inactive'}) [y/n]: ").strip().lower()
                    if new_status in ['y', 'yes']:
                        updates["is_active"] = True
                    elif new_status in ['n', 'no']:
                        updates["is_active"] = False
                
                if updates:
                    if self.manager.update_classification_rule(rule.rule_id, updates):
                        self.manager.save_to_file()
                        print(f"\n✅ Successfully updated rule: {rule.rule_id}")
                    else:
                        print(f"\n❌ Failed to update rule: {rule.rule_id}")
                else:
                    print("\n❌ No changes made")
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    def test_rules(self):
        """Test rules with sample data."""
        print("\n" + "="*60)
        print("TEST BUSINESS RULES")
        print("="*60)
        
        test_cases = [
            ("Office Supplies - Stationery", 500.00),
            ("Computer Equipment - Laptops", 15000.00),
            ("Vendor Payment - Professional Services", 25000.00),
            ("Employee Salary - Monthly", 8000.00),
            ("Administrative Overhead", 2000.00)
        ]
        
        print("Testing classification rules with sample data:")
        print("-" * 50)
        
        for description, amount in test_cases:
            print(f"\nDescription: {description}")
            print(f"Amount: ${amount:,.2f}")
            
            # Find matching classification rule
            best_match = None
            best_score = 0
            
            for rule in self.manager.get_classification_rules():
                score = 0
                desc_lower = description.lower()
                
                # Check keywords
                for keyword in rule.keywords:
                    if keyword.lower() in desc_lower:
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_match = rule
            
            if best_match:
                print(f"✅ Matched: {best_match.rule_id} - {best_match.name}")
                print(f"   Category: {best_match.category} | Subcategory: {best_match.subcategory}")
                print(f"   Priority: {best_match.priority}")
            else:
                print("❌ No match found")
            
            # Check approval rule
            if best_match:
                approval_rule = self.manager.get_approval_rule(amount, best_match.category)
                if approval_rule:
                    print(f"   Approval: {approval_rule.approval_level}")
                    print(f"   Approvers: {', '.join(approval_rule.required_approvers)}")
    
    def export_rules(self):
        """Export rules to a file."""
        print("\n" + "="*60)
        print("EXPORT BUSINESS RULES")
        print("="*60)
        
        filename = input("Export filename (default: business_rules_export.json): ").strip()
        if not filename:
            filename = "business_rules_export.json"
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        self.manager.export_rules(filename)
        print(f"✅ Rules exported to {filename}")
    
    def import_rules(self):
        """Import rules from a file."""
        print("\n" + "="*60)
        print("IMPORT BUSINESS RULES")
        print("="*60)
        
        filename = input("Import filename: ").strip()
        if not filename:
            print("❌ Filename is required")
            return
        
        if not Path(filename).exists():
            print(f"❌ File {filename} does not exist")
            return
        
        confirm = input(f"Import rules from {filename}? This will replace current rules. [y/n]: ").strip().lower()
        if confirm in ['y', 'yes']:
            self.manager.import_rules(filename)
            self.manager.save_to_file()
            print(f"✅ Rules imported from {filename}")
        else:
            print("❌ Import cancelled")
    
    def validate_rules(self):
        """Validate all rules."""
        print("\n" + "="*60)
        print("VALIDATE BUSINESS RULES")
        print("="*60)
        
        errors = self.manager.validate_rules()
        
        if not errors:
            print("✅ All rules are valid!")
        else:
            print("❌ Validation errors found:")
            for error in errors:
                print(f"   - {error}")
    
    def run(self):
        """Run the interactive editor."""
        print("Welcome to the Payment Voucher Business Rules Editor!")
        print("This tool helps you manage business rules without coding.")
        
        while True:
            self.show_main_menu()
            choice = input("\nSelect an option (0-9): ").strip()
            
            if choice == "0":
                print("\n👋 Goodbye! Don't forget to save your changes.")
                break
            elif choice == "1":
                self.view_rules()
            elif choice == "2":
                self.add_classification_rule()
            elif choice == "3":
                self.modify_classification_rule()
            elif choice == "4":
                print("🚧 Approval rules editor coming soon!")
            elif choice == "5":
                print("🚧 Validation rules editor coming soon!")
            elif choice == "6":
                self.test_rules()
            elif choice == "7":
                self.export_rules()
            elif choice == "8":
                self.import_rules()
            elif choice == "9":
                self.validate_rules()
            else:
                print("❌ Invalid option. Please choose 0-9.")
            
            input("\nPress Enter to continue...")


def main():
    """Main entry point."""
    editor = BusinessRulesEditor()
    editor.run()


if __name__ == "__main__":
    main()
