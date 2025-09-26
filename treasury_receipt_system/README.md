# Treasury Receipt Automation System

Parse transactions, validate against Excel reference data, classify (Interest vs Principal), group, and generate Treasury Receipts. Fully on-prem; optional local LLM hook.

## Install
```bash
pip install -r requirements.txt
```

## Run
```bash
python -m treasury_receipt_system.main --excel ADERP_COA_2025.xlsx --input "201.2010023.102148.1.000000.000000.000000 - Debit: 50000"
```

Or read from a file:
```bash
python -m treasury_receipt_system.main --excel ADERP_COA_2025.xlsx --input-file sample_input.txt
```

Write output to a file:
```bash
python -m treasury_receipt_system.main --excel ADERP_COA_2025.xlsx --input-file sample_input.txt --output-file receipt.txt
```

## Tests
```bash
pytest -q
```

## Local LLM
Implement `LocalLLMClassifier.classify()` in `business_rules.py` to call an on-prem model (e.g., Qwen). Heuristics are used if not configured.
