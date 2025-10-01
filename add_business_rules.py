#!/usr/bin/env python3
"""
Quick script to add business rules from your users.

This script helps you quickly add new business rules that your users have provided
without needing to use the full interactive editor.
"""

import sys
from pathlib import Path

# Add the treasury_receipt_system to the path
sys.path.insert(0, str(Path(__file__).parent / "treasury_receipt_system"))

from treasury_receipt_system.payment_voucher.business_rules_config import (
    BusinessRulesManager, ClassificationRule
)


def add_rule_interactive():
    """Add a single rule interactively."""
    print("Add New Business Rule")
    print("=" * 40)
    
    manager = BusinessRulesManager()
    
    # Get rule details
    rule_id = input("Rule ID (e.g., OP-004): ").strip()
    if not rule_id:
        print("❌ Rule ID is required")
        return
    
    name = input("Rule Name: ").strip()
    description = input("Description: ").strip()
    
    print("\nKeywords (comma-separated):")
    keywords_input = input("e.g., office supplies, stationery: ").strip()
    keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
    
    print("\nGL Account Patterns (comma-separated):")
    gl_patterns_input = input("e.g., 6*, 601*: ").strip()
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
    
    subcategory = input("Subcategory: ").strip()
    
    try:
        priority = int(input("Priority (default 100): ").strip() or "100")
    except ValueError:
        priority = 100
    
    # Create and add the rule
    rule = ClassificationRule(
        rule_id=rule_id,
        name=name,
        description=description,
        keywords=keywords,
        gl_account_patterns=gl_patterns,
        amount_ranges=[{"min": 0, "max": 1000000}],
        category=category,
        subcategory=subcategory,
        priority=priority,
        is_active=True,
        created_by="Business User",
        created_date="",
        last_modified=""
    )
    
    manager.add_classification_rule(rule)
    manager.save_to_file()
    
    print(f"\n✅ Successfully added rule: {rule_id}")
    print(f"   Category: {category} | Subcategory: {subcategory}")
    print(f"   Keywords: {', '.join(keywords)}")


def add_rule_from_template():
    """Add a rule using a predefined template."""
    print("Add Rule from Template")
    print("=" * 40)
    
    templates = {
        "1": {
            "name": "Travel Expenses",
            "keywords": ["travel", "transportation", "accommodation", "meals", "hotel", "flight"],
            "gl_patterns": ["6*", "604*"],
            "category": "Operating",
            "subcategory": "Travel"
        },
        "2": {
            "name": "Training and Development",
            "keywords": ["training", "education", "certification", "workshop", "course", "learning"],
            "gl_patterns": ["6*", "605*"],
            "category": "Operating", 
            "subcategory": "Training"
        },
        "3": {
            "name": "Marketing and Advertising",
            "keywords": ["marketing", "advertising", "promotion", "publicity", "campaign"],
            "gl_patterns": ["6*", "606*"],
            "category": "Operating",
            "subcategory": "Marketing"
        },
        "4": {
            "name": "Legal and Professional Services",
            "keywords": ["legal", "lawyer", "attorney", "professional services", "consulting"],
            "gl_patterns": ["6*", "607*"],
            "category": "Operating",
            "subcategory": "Professional Services"
        },
        "5": {
            "name": "Insurance",
            "keywords": ["insurance", "premium", "coverage", "policy"],
            "gl_patterns": ["6*", "608*"],
            "category": "Operating",
            "subcategory": "Insurance"
        }
    }
    
    print("Available templates:")
    for key, template in templates.items():
        print(f"{key}. {template['name']}")
    
    choice = input("\nSelect template (1-5): ").strip()
    if choice not in templates:
        print("❌ Invalid choice")
        return
    
    template = templates[choice]
    
    # Get rule ID
    rule_id = input(f"Rule ID for {template['name']} (e.g., OP-{choice.zfill(3)}): ").strip()
    if not rule_id:
        print("❌ Rule ID is required")
        return
    
    # Add any additional keywords
    additional_keywords = input("Additional keywords (comma-separated, optional): ").strip()
    if additional_keywords:
        template["keywords"].extend([k.strip() for k in additional_keywords.split(",") if k.strip()])
    
    # Create the rule
    manager = BusinessRulesManager()
    rule = ClassificationRule(
        rule_id=rule_id,
        name=template["name"],
        description=f"Business rule for {template['name'].lower()}",
        keywords=template["keywords"],
        gl_account_patterns=template["gl_patterns"],
        amount_ranges=[{"min": 0, "max": 1000000}],
        category=template["category"],
        subcategory=template["subcategory"],
        priority=100,
        is_active=True,
        created_by="Business User",
        created_date="",
        last_modified=""
    )
    
    manager.add_classification_rule(rule)
    manager.save_to_file()
    
    print(f"\n✅ Successfully added rule: {rule_id}")
    print(f"   {template['name']} - {template['category']}")


def show_current_rules():
    """Show current business rules."""
    print("Current Business Rules")
    print("=" * 40)
    
    manager = BusinessRulesManager()
    
    for rule in manager.config.classification_rules:
        status = "✅" if rule.is_active else "❌"
        print(f"{status} {rule.rule_id}: {rule.name}")
        print(f"   Category: {rule.category} | Subcategory: {rule.subcategory}")
        print(f"   Keywords: {', '.join(rule.keywords[:3])}{'...' if len(rule.keywords) > 3 else ''}")
        print()


def test_rules():
    """Test current rules with sample data."""
    print("Test Business Rules")
    print("=" * 40)
    
    manager = BusinessRulesManager()
    
    test_cases = [
        ("Office Supplies - Stationery", 500.00),
        ("Travel - Hotel Accommodation", 1200.00),
        ("Training - Professional Development", 2500.00),
        ("Marketing - Advertising Campaign", 15000.00),
        ("Legal - Contract Review", 5000.00)
    ]
    
    for description, amount in test_cases:
        print(f"\nDescription: {description}")
        print(f"Amount: ${amount:,.2f}")
        
        # Find matching rule
        best_match = None
        best_score = 0
        
        for rule in manager.get_classification_rules():
            score = 0
            desc_lower = description.lower()
            
            for keyword in rule.keywords:
                if keyword.lower() in desc_lower:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = rule
        
        if best_match:
            print(f"✅ Matched: {best_match.rule_id} - {best_match.name}")
            print(f"   Category: {best_match.category} | Subcategory: {best_match.subcategory}")
        else:
            print("❌ No match found")


def main():
    """Main menu."""
    print("Business Rules Quick Add Tool")
    print("=" * 40)
    print("1. Add new rule interactively")
    print("2. Add rule from template")
    print("3. Show current rules")
    print("4. Test current rules")
    print("0. Exit")
    
    choice = input("\nSelect option (0-4): ").strip()
    
    if choice == "1":
        add_rule_interactive()
    elif choice == "2":
        add_rule_from_template()
    elif choice == "3":
        show_current_rules()
    elif choice == "4":
        test_rules()
    elif choice == "0":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()
