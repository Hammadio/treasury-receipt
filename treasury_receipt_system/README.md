# Treasury Receipt / Payment Voucher Automation System

Parse transactions, validate against Excel reference data, classify transactions, group, and generate Treasury Receipts or Payment Vouchers. Fully on-prem; optional local LLM hook.

## 🚀 New: Payment Voucher Creation Agent

The system now includes a comprehensive **Payment Voucher Creation Agent** with advanced features:

- **Smart Classification**: Automatically categorizes transactions (Operating, Capital, Vendor, Personnel, Administrative)
- **Approval Workflows**: Built-in approval processes based on amount thresholds and risk levels
- **Validation Engine**: Comprehensive business rules and compliance checking
- **Multiple Templates**: Standard, Executive, and Simple voucher formats
- **Modular Architecture**: Clean separation of concerns for easy customization

## Install
```bash
pip install -r requirements.txt
```

## Quick Start

### Treasury Receipt Mode (Legacy)
```bash
python -m treasury_receipt_system.main --excel ADERP_COA_2025.xlsx --input "201.2010023.102148.1.000000.000000.000000 - Debit: 50000"
```

### Payment Voucher Mode (New)
```bash
python -m treasury_receipt_system.main --excel ADERP_COA_2025.xlsx --mode payment_voucher --input "201.2010023.102148.1.000000.000000.000000 - Debit: 5000"
```

## File Input/Output
```bash
# Treasury Receipts
python -m treasury_receipt_system.main --excel ADERP_COA_2025.xlsx --input-file sample_input.txt --output-file receipt.txt

# Payment Vouchers
python -m treasury_receipt_system.main --excel ADERP_COA_2025.xlsx --mode payment_voucher --input-file sample_input_payment_voucher.txt --output-file voucher.txt
```

## Payment Voucher Features

### Classification Categories
- **Operating**: Office supplies, utilities, travel, training, consulting
- **Capital**: Equipment, furniture, software, infrastructure, vehicles
- **Vendor**: Service providers, suppliers, contractors
- **Personnel**: Salaries, benefits, bonuses, compensation
- **Administrative**: General overhead, management, compliance

### Approval Levels
- **Standard** (< $10K): Department Head → Finance Processing
- **High** ($10K - $100K): Department Head → Finance Director → Finance Processing
- **Executive** ($100K+): Department Head → Finance Director → Executive → Finance Processing

### Validation Features
- Amount thresholds and limits
- GL account validation
- Budget availability checks
- Compliance requirements
- Risk assessment

## Advanced Usage

### Using the Payment Voucher Processor Directly
```python
from treasury_receipt_system.payment_voucher.processor import PaymentVoucherProcessor

processor = PaymentVoucherProcessor(enable_llm=True)

result = processor.process_transactions(
    excel_path="ADERP_COA_2025.xlsx",
    input_text="your transaction data here",
    created_by="Your Name",
    department="Your Department",
    template_style="executive"  # standard, executive, simple
)

if result["success"]:
    for voucher in result["vouchers"]:
        print(f"Voucher: {voucher['voucher_number']}")
        print(f"Category: {voucher['classification'].category}")
        print(f"Amount: ${voucher['amount']:,.2f}")
```

### Custom Classification
```python
from treasury_receipt_system.payment_voucher.voucher_classifier import PaymentVoucherClassifier

classifier = PaymentVoucherClassifier(enable_llm=True)
classification = classifier.classify_transaction(
    gl_description="Office Supplies - Stationery",
    amount=500.00,
    additional_context={"department": "Finance"}
)
```

### Validation
```python
from treasury_receipt_system.payment_voucher.voucher_validator import VoucherValidator

validator = VoucherValidator()
validation_result = validator.validate_voucher(
    account_desc=account_desc,
    amount=amount,
    classification=classification
)

if not validation_result.is_valid:
    print("Validation errors:", validation_result.errors)
```

## Examples

Run the comprehensive examples:
```bash
python example_payment_voucher_usage.py
```

## System Architecture

### Core Modules
- **`main.py`**: CLI interface and routing
- **`account_parser.py`**: Account number parsing and validation
- **`reference_lookup.py`**: Excel COA data loading
- **`business_rules.py`**: Legacy Treasury Receipt rules

### Payment Voucher Modules
- **`payment_voucher/processor.py`**: Main orchestrator
- **`payment_voucher/voucher_classifier.py`**: Smart classification
- **`payment_voucher/voucher_generator.py`**: Voucher generation
- **`payment_voucher/approval_workflow.py`**: Approval management
- **`payment_voucher/voucher_validator.py`**: Validation engine

## Configuration

### Environment Variables
```bash
# LLM Configuration (optional)
export LLM_ENDPOINT="http://localhost:8000/v1"
export LLM_MODEL="Qwen3-8B-Instruct"
export LLM_API_KEY="sk-local"
```

### Template Styles
- **standard**: Full-featured vouchers with approval workflows
- **executive**: Enhanced vouchers with risk assessment
- **simple**: Basic vouchers for quick processing

## Tests
```bash
pytest -q
```

## Migration from Treasury Receipts

The system maintains full backward compatibility. Existing Treasury Receipt functionality remains unchanged. To use Payment Vouchers:

1. Add `--mode payment_voucher` to your commands
2. Use the new sample input file: `sample_input_payment_voucher.txt`
3. Optionally customize classification rules in `voucher_classifier.py`

## Support

For questions or customization needs, the modular architecture allows easy modification of:
- Classification rules
- Approval workflows
- Validation criteria
- Voucher templates
- Business logic
