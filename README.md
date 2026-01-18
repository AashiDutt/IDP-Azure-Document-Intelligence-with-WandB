# Invoice IDP Pipeline with ABBYY + W&B

A finance-grade invoice processing pipeline that demonstrates how to build production-ready document automation with ABBYY IDP and Weights & Biases observability.

## Architecture

```
Invoices (PDF/Image)
        ↓
ABBYY IDP (API / Cloud / Vantage)
        ↓
Orchestration code (Python service)
        ↓
Canonical schema + validation + routing
        ↓
Weights & Biases (SDK)
```

## Overview

This project implements an end-to-end Accounts Payable (AP) invoice workflow that:

- Runs invoices through vendor extractors (treated as black boxes)
- Normalizes outputs into a canonical schema with full audit trails
- Applies finance-grade validation and routing logic
- Logs everything to Weights & Biases for observability and analytics

## Key Features

### 1. Canonical Schema with Audit Pack

Every extracted field includes:
- `value`: The extracted value
- `confidence`: Vendor/model confidence score
- `evidence`: Page number and bounding box/text anchor
- `pipeline_version`: Code and ruleset version
- `vendor_version`: Extractor version

### 2. Finance-Grade Validation

- **Schema constraints**: Required fields, date formats, currency codes
- **Reconciliation rules**: `abs(subtotal + tax - total) < tolerance`
- **Policy rules**: High total thresholds, missing PO detection
- **Confidence thresholds**: Configurable per field

### 3. Routing with Reason Codes

Each document gets a clear outcome:
- `AUTO_POST`: Ready for automatic posting
- `NEEDS_REVIEW`: Requires manual review

With explicit reason codes:
- `TOTAL_MISMATCH`: Reconciliation failed
- `LOW_CONFIDENCE`: Confidence below threshold
- `HIGH_TOTAL`: Exceeds manual review threshold
- `MISSING_PO`: Purchase order number missing
- `MISSING_REQUIRED_FIELDS`: Critical fields absent

### 4. W&B Observability

- **Artifacts**: Versioned datasets (raw invoices, predictions, ground truth)
- **Run tracking**: All configs and parameters logged
- **Tables**: One row per document with all metrics
- **Dashboards**: Error slicing, accuracy metrics, exception rates

## Project Structure

```
.
├── demo.py                # Main demo script
├── orchestrator.py        # Pipeline orchestrator
├── abbyy_adapter.py       # ABBYY IDP connector
├── schema.py              # Canonical schema definitions
├── normalizer.py          # Vendor output → canonical schema
├── validator.py           # Validation and routing logic
├── data_generator.py      # Test data generation
├── vendor_extractor.py    # Simulator (for testing)
├── config.yaml            # Config template
├── requirements.txt       # Dependencies
└── SETUP.md              # Setup instructions
```

## Installation

```bash
pip install -r requirements.txt
wandb login
```

## Quick Start

### Demo Mode (No ABBYY API Required)

```bash
python demo.py
```

Generates test invoices and processes them with a simulator to demonstrate the pipeline.

### With Real ABBYY IDP

See [SETUP.md](SETUP.md) for detailed instructions.

```bash
# 1. Get ABBYY credentials (FlexiCapture Cloud, Vantage, or Cloud OCR)
# 2. Configure
cp config.yaml config_local.yaml
# Edit config_local.yaml with your ABBYY credentials and set use_simulator: false

# 3. Add invoice files
mkdir sample_invoices
# Place PDF/image invoices in sample_invoices/

# 4. Run
python demo.py --real
```

### Process Single Invoice

```bash
python demo.py --single
```

## Output

The pipeline generates:

- `ground_truth.json`: Ground truth dataset
- `test_data.json`: Test invoices
- W&B dashboard with:
  - Tables showing per-document metrics
  - Aggregate accuracy metrics
  - Error slicing by reason code
  - Versioned artifacts

## Customization

### Adjust Validation Thresholds

Edit `validator.py` or pass parameters:

```python
validator = Validator(
    low_confidence_threshold=0.8,
    high_total_threshold=50000.0,
    currency_tolerance={"USD": 0.01, "EUR": 0.01}
)
```

### Add New Vendors

1. Add extraction logic in `vendor_extractor.py`
2. Add normalization logic in `normalizer.py`
3. Update the pipeline to use the new vendor

### Modify Schema

Edit `schema.py` to add/remove fields. The validation logic in `validator.py` will need updates accordingly.

## Why This Approach Works

This setup makes failures:

- **Visible**: Sliced by reason code, not just averaged
- **Explainable**: Clear rules + evidence for each decision
- **Actionable**: Specific reason codes guide fixes
- **Auditable**: Versioned inputs, configs, and outputs

This turns "demo accuracy" into **production-grade document automation**.

## ABBYY Platform Options

This pipeline supports three ABBYY platforms:

1. **ABBYY FlexiCapture Cloud** - Easiest to get started, invoice-specific workflows
2. **ABBYY Vantage** - Enterprise-grade, multi-skill processing
3. **ABBYY Cloud OCR SDK** - Basic OCR with custom parsing

See [SETUP.md](SETUP.md) for platform-specific configuration.

## Next Steps

1. ✅ Run demo with simulator to understand the flow
2. ✅ Set up ABBYY credentials (choose FlexiCapture Cloud for easiest start)
3. ✅ Process 10-20 real invoices
4. ✅ Review results in W&B dashboard
5. ✅ Adjust validation thresholds based on your business rules
6. ✅ Deploy with continuous monitoring via W&B

## License

MIT

