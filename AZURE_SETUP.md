# Azure Document Intelligence + W&B Setup

Process invoices with Azure Document Intelligence and log everything to W&B for observability.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Login to W&B
wandb login

# 3. Run pipeline
python run_azure_pipeline.py
```

## What It Does

```
Invoices (PDF/Image/URL)
        ↓
Azure Document Intelligence (prebuilt-invoice model)
        ↓
Canonical schema normalization
        ↓
Validation + Routing
        ↓
W&B observability (JSON + Tables + Metrics)
```

## Using Your Own Invoices

### Option 1: URLs

Edit `run_azure_pipeline.py`:

```python
invoices = [
    "https://example.com/invoice1.pdf",
    "https://example.com/invoice2.jpg",
]
```

### Option 2: Local Files

```bash
# Create directory and add files
mkdir sample_invoices
# Add your PDFs, images, etc.

# The script will automatically find them
python run_azure_pipeline.py
```

### Option 3: Mix Both

```python
invoices = [
    "https://example.com/invoice1.pdf",
    "sample_invoices/invoice_local.pdf",
    "sample_invoices/invoice_scan.jpg",
]
```

## Output

### 1. JSON File (`azure_results.json`)

Complete extraction results with:
- All extracted fields
- Confidence scores
- Validation results
- Routing decisions

Example:
```json
{
  "doc_id": "INV-001",
  "extraction": {
    "vendor": "azure_document_intelligence",
    "fields": {
      "invoice_number": {"value": "INV-12345", "confidence": 0.98},
      "total": {"value": 1234.56, "confidence": 0.95}
    }
  },
  "validation": {
    "passed": true,
    "checks": {...}
  },
  "routing": {
    "outcome": "AUTO_POST",
    "confidence": 0.92,
    "reason_codes": []
  }
}
```

### 2. W&B Dashboard

Interactive tables with:
- Per-invoice results
- Confidence scores
- Validation pass/fail
- Routing decisions
- Reason codes

Metrics:
- Auto-post rate
- Validation pass rate
- Average confidence scores
- Success/failure counts

Artifacts:
- JSON results file (versioned)
- All configs and parameters

## Configuration

### Azure Credentials

The script uses the credentials from your `test.py`. To change:

Edit `run_azure_pipeline.py`:
```python
AZURE_ENDPOINT = "https://YOUR-RESOURCE.cognitiveservices.azure.com/"
AZURE_KEY = "YOUR_API_KEY"
```

### Validation Thresholds

Edit in `run_azure_pipeline.py`:
```python
self.validator = Validator(
    low_confidence_threshold=0.7,    # Min confidence for auto-post
    high_total_threshold=100000.0,   # Amount requiring review
    currency_tolerance={"USD": 0.01} # Reconciliation tolerance
)
```

### W&B Project

Change project name:
```python
pipeline = AzurePipeline(
    azure_endpoint=AZURE_ENDPOINT,
    azure_key=AZURE_KEY,
    wandb_project="my-invoice-project"  # Your project name
)
```

## Supported File Formats

- PDF (.pdf)
- Images (.jpg, .jpeg, .png, .tiff, .tif, .bmp)
- URLs (must be publicly accessible)

## Example Workflows

### Process Single Invoice

```python
from run_azure_pipeline import AzurePipeline

pipeline = AzurePipeline(ENDPOINT, KEY)

result = pipeline.process_invoice(
    "sample_invoices/invoice.pdf",
    doc_id="MY-INV-001"
)

# Access JSON output
print(result["json_output"])

pipeline.finish()
```

### Process Batch with Custom Output

```python
pipeline = AzurePipeline(ENDPOINT, KEY)

invoices = [
    "invoice1.pdf",
    "invoice2.pdf",
    "https://example.com/invoice3.jpg"
]

results = pipeline.process_batch(
    invoices,
    output_file="my_results.json"
)

pipeline.finish()
```

### Get Specific Fields

```python
result = pipeline.process_invoice("invoice.pdf")

json_data = result["json_output"]

# Access extracted data
invoice_num = json_data["normalized"]["invoice_number"]
total = json_data["normalized"]["total"]
confidence = json_data["normalized"]["confidence_scores"]["total"]

# Check routing
if json_data["routing"]["outcome"] == "AUTO_POST":
    print("Ready for automatic posting!")
else:
    print(f"Needs review: {json_data['routing']['reason_codes']}")
```

## What You Get in W&B

### Tables
- One row per invoice
- All extracted fields
- Confidence scores per field
- Validation results
- Routing decisions
- Reason codes for review cases

### Metrics
- `total_invoices`: Number processed
- `successful`: Successful extractions
- `failed`: Failed extractions
- `auto_post_rate`: % ready for auto-post
- `validation_pass_rate`: % passing validation
- `avg_confidence`: Average confidence across invoices

### Artifacts
- `invoice_results`: JSON file with all data (versioned)

## Troubleshooting

### "No module named 'azure'"
```bash
pip install azure-ai-documentintelligence azure-core
```

### "Authentication failed"
- Check `AZURE_ENDPOINT` is correct
- Verify `AZURE_KEY` is active
- Ensure endpoint matches key region

### "File not found"
- Verify file path is correct
- Check file exists in `sample_invoices/`
- For URLs, ensure they're publicly accessible

### Low confidence scores
- Check image/PDF quality
- Ensure invoice is clearly scanned
- Try different invoice layouts
- Consider using custom model for specific layouts

## Comparing with ABBYY

You can compare Azure vs ABBYY results:

1. Run Azure pipeline:
   ```bash
   python run_azure_pipeline.py
   ```

2. Run ABBYY pipeline (if configured):
   ```bash
   python demo.py --real
   ```

3. Compare in W&B dashboard:
   - View both projects
   - Compare confidence scores
   - Compare auto-post rates
   - Analyze failure reasons

## Next Steps

1. [x] Run with sample invoice
2. [x] Add your own invoices
3. [x] Review results in W&B
4. [x] Adjust validation thresholds
5. [x] Set up automated processing
6. [x] Monitor accuracy over time

## Support

- Azure Docs: https://learn.microsoft.com/azure/ai-services/document-intelligence/
- W&B Docs: https://docs.wandb.ai/
- W&B Community: https://community.wandb.ai/

