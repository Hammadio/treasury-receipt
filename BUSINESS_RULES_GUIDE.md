# Business Rules Management Guide

This guide helps you manage business rules for the Payment Voucher Creation Agent based on feedback from your budgeting team.

## 🎯 Overview

The Payment Voucher system now uses a flexible business rules engine that allows you to:
- Add new classification rules without coding
- Modify existing rules based on user feedback
- Test rules before applying them
- Export/import rules for backup and sharing

## 📁 Files Overview

- **`business_rules.json`** - Main configuration file (auto-generated)
- **`business_rules_editor.py`** - Full interactive editor
- **`add_business_rules.py`** - Quick rule addition tool
- **`business_rules_config.py`** - Core rules engine

## 🚀 Quick Start

### 1. Add a Single Rule (Recommended for beginners)

```bash
python add_business_rules.py
```

Choose option 1 to add a rule interactively, or option 2 to use a template.

### 2. Use the Full Editor (For advanced users)

```bash
python business_rules_editor.py
```

This provides a complete interface for managing all aspects of business rules.

## 📋 Rule Types

### Classification Rules
Define how transactions are categorized based on:
- **Keywords** in the description
- **GL Account patterns** (e.g., "6*" for expense accounts)
- **Amount ranges** (e.g., $0-$10,000)
- **Priority** (higher numbers = more important)

### Approval Rules
Define approval workflows based on:
- **Amount thresholds**
- **Transaction categories**
- **Required approvers**
- **Escalation rules**

### Validation Rules
Define validation requirements:
- **Amount limits**
- **GL account validation**
- **Compliance checks**
- **Error messages**

## 🔧 Common Scenarios

### Scenario 1: User says "Office supplies should be classified as Operating Expenses"

**Solution:**
1. Run `python add_business_rules.py`
2. Choose option 1 (Add new rule interactively)
3. Enter:
   - Rule ID: `OP-004`
   - Name: `Office Supplies`
   - Keywords: `office supplies, stationery, pens, paper, notebooks`
   - GL Patterns: `6*, 601*`
   - Category: `Operating`
   - Subcategory: `Office Supplies`

### Scenario 2: User says "Travel expenses over $5,000 need executive approval"

**Solution:**
1. Use the full editor: `python business_rules_editor.py`
2. Go to "Add Approval Rule"
3. Set conditions: amount > $5,000, category = Operating
4. Set approval level: Executive
5. Add required approvers

### Scenario 3: User says "Vendor payments need special validation"

**Solution:**
1. Use the full editor: `python business_rules_editor.py`
2. Go to "Add Validation Rule"
3. Set rule type: `compliance`
4. Set conditions: category = Vendor
5. Add required checks: vendor_verification, contract_validation

## 📊 Testing Rules

### Test Individual Rules
```bash
python add_business_rules.py
# Choose option 4 (Test current rules)
```

### Test with Real Data
```bash
python -m treasury_receipt_system.main --excel ADERP_COA_2025.xlsx --mode payment_voucher --input "your test transaction" --no-llm
```

## 🔄 Rule Management

### View Current Rules
```bash
python add_business_rules.py
# Choose option 3 (Show current rules)
```

### Export Rules (Backup)
```bash
python business_rules_editor.py
# Choose option 7 (Export rules)
```

### Import Rules (Restore)
```bash
python business_rules_editor.py
# Choose option 8 (Import rules)
```

## 📝 Rule Examples

### Example 1: Office Supplies
```json
{
  "rule_id": "OP-001",
  "name": "Office Supplies",
  "keywords": ["office supplies", "stationery", "pens", "paper"],
  "gl_account_patterns": ["6*", "601*"],
  "category": "Operating",
  "subcategory": "Office Supplies",
  "priority": 100
}
```

### Example 2: IT Equipment
```json
{
  "rule_id": "CAP-001", 
  "name": "IT Equipment",
  "keywords": ["computer", "laptop", "software", "hardware"],
  "gl_account_patterns": ["1*", "11*"],
  "category": "Capital",
  "subcategory": "IT Equipment",
  "priority": 100
}
```

### Example 3: High-Value Approval
```json
{
  "rule_id": "APP-003",
  "name": "Executive Approval",
  "conditions": {"min_amount": 100000},
  "approval_level": "Executive",
  "required_approvers": ["Department Head", "Finance Director", "Executive"]
}
```

## ⚠️ Best Practices

### 1. Rule Naming
- Use consistent prefixes: `OP-` for Operating, `CAP-` for Capital, etc.
- Use descriptive names: "Office Supplies" not "Rule1"
- Include version numbers for major changes: "OP-001-v2"

### 2. Keywords
- Use specific terms: "office supplies" not "supplies"
- Include variations: "computer", "laptop", "desktop"
- Test keywords with real transaction descriptions

### 3. GL Account Patterns
- Use wildcards: "6*" for all expense accounts
- Be specific when needed: "601*" for specific expense types
- Test patterns with your actual GL accounts

### 4. Priority
- Higher numbers = higher priority
- Specific rules should have higher priority than general ones
- Default: 100 for most rules, 50 for catch-all rules

### 5. Testing
- Always test new rules before deploying
- Test with edge cases and unusual descriptions
- Validate with your business users

## 🚨 Troubleshooting

### Rule Not Matching
1. Check keywords are spelled correctly
2. Verify GL account patterns match your COA
3. Ensure amount is within specified ranges
4. Check rule priority and active status

### Wrong Classification
1. Review keyword matches
2. Check for conflicting rules
3. Adjust rule priority
4. Add more specific keywords

### Approval Issues
1. Verify approval rules are active
2. Check amount thresholds
3. Ensure approver roles are correct
4. Review escalation rules

## 📞 Support

If you need help with business rules:

1. **Check the logs** - Look for error messages in the console output
2. **Test with simple cases** - Start with basic rules and build up
3. **Use the validation tool** - Run rule validation to check for errors
4. **Export and backup** - Always backup your rules before major changes

## 🔄 Workflow for Adding User Feedback

1. **Gather Requirements** - Get specific details from users
2. **Add Rule** - Use `add_business_rules.py` for quick additions
3. **Test Rule** - Test with sample data
4. **Validate** - Run validation to check for errors
5. **Deploy** - Rules are automatically active after saving
6. **Monitor** - Watch for any issues in production
7. **Iterate** - Refine rules based on results

Remember: The system is designed to be flexible and user-friendly. Don't hesitate to experiment with rules - you can always modify or remove them if needed!
