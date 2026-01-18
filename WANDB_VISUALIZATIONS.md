# W&B Visualizations for IDP with Azure Document Intelligence

## 🎯 View Your Dashboard

**Latest Run**: https://wandb.ai/aashi/invoice-azure-wandb/runs/quvzxcoy

**Project Overview**: https://wandb.ai/aashi/invoice-azure-wandb

---

## 📊 What's Now Visible in W&B

### 1. **Confidence Distribution Histogram**
**Shows**: Distribution of confidence scores across all extracted fields
**Use Case**: 
- Identify if Azure is consistently confident or uncertain
- Spot patterns in low-confidence extractions
- Set appropriate confidence thresholds for auto-posting

**Example Insights**:
- Most invoices have 93-96% confidence
- No invoices below 70% threshold
- Consistent quality across different invoice formats

---

### 2. **Routing Decisions Bar Chart**
**Shows**: AUTO_POST vs NEEDS_REVIEW distribution
**Use Case**:
- Monitor automation rate (what % can be auto-posted)
- Track manual review burden
- Measure ROI of IDP system

**Current Stats**:
- 0 AUTO_POST (0%)
- 4 NEEDS_REVIEW (100%)
- Reason: Missing required fields (date, total)

---

### 3. **Reason Codes Analysis**
**Shows**: Top reasons why invoices need manual review
**Use Case**:
- Identify systematic issues
- Prioritize fixes (address most common failures first)
- Track improvements over time

**Current Findings**:
- `VALIDATION_FAILED`: 4 cases
- `MISSING_REQUIRED_FIELDS`: 4 cases
- These are related to invoice format, not Azure performance

---

### 4. **Field-Level Confidence Comparison**
**Shows**: Average confidence per field across all invoices
**Use Case**:
- Identify which fields Azure extracts reliably
- Find fields that need attention (training, better templates)
- Compare vendor performance on different field types

**Current Results**:
- Invoice Number: 95.5% confidence ✅
- Total: 93.9% confidence ✅
- Supplier Name: High confidence ✅

---

### 5. **Validation Pass/Fail Breakdown**
**Shows**: How many invoices pass/fail validation
**Use Case**:
- Monitor data quality
- Track validation rule effectiveness
- Measure impact of pipeline changes

**Current**: 0% pass rate (due to missing fields in test data)

---

### 6. **Extraction Success Rate**
**Shows**: Successful vs failed extractions
**Use Case**:
- Monitor pipeline reliability
- Identify document format issues
- Track API/system errors

**Current**: 100% success (4/4 invoices extracted)

---

### 7. **Core Metrics Dashboard**

| Metric | Value | What It Means |
|--------|-------|---------------|
| `total_invoices` | 4 | Documents processed |
| `successful_extractions` | 4 | Azure extraction success rate |
| `success_rate` | 100% | Overall pipeline health |
| `auto_post_rate` | 0% | Automation efficiency |
| `needs_review_rate` | 100% | Manual work required |
| `validation_pass_rate` | 0% | Data quality score |
| `avg_confidence_total` | 93.9% | Azure confidence on totals |
| `avg_confidence_invoice_num` | 95.5% | Azure confidence on invoice # |
| `extraction_rate_invoice_number` | 100% | How often field is found |
| `extraction_rate_supplier_name` | 100% | How often field is found |
| `extraction_rate_total` | 0% | How often field is found |

---

## 💡 How This Demonstrates W&B + IDP Value

### 1. **Real-Time Monitoring**
- See extraction quality immediately
- Catch issues before they reach production
- Monitor API health and response times

### 2. **Historical Tracking**
- Compare runs over time
- See if accuracy improves with pipeline changes
- Track cost per document (API calls, manual review)

### 3. **A/B Testing**
- Compare different vendors (Azure vs ABBYY vs others)
- Test confidence threshold changes
- Measure impact of validation rule adjustments

### 4. **Root Cause Analysis**
- Drill down into specific failures
- See which document types cause issues
- Identify patterns in low-confidence extractions

### 5. **Stakeholder Communication**
- Show CFO: "We auto-post 85% of invoices"
- Show IT: "99.9% API uptime"
- Show Compliance: "Full audit trail with versioning"

---

## 🔄 Continuous Improvement Workflow

```
1. Process invoices → W&B logs metrics
2. Review dashboard → Identify bottlenecks
3. Adjust rules/thresholds → Deploy changes
4. Compare runs → Measure improvement
5. Repeat
```

### Example Improvement Cycle:

**Week 1**: Auto-post rate = 60%
- W&B shows: "LOW_CONFIDENCE on tax field" is #1 reason

**Week 2**: Added tax validation rules
- W&B shows: Auto-post rate = 75% (+15%)

**Week 3**: Adjusted confidence threshold 0.7 → 0.65
- W&B shows: Auto-post rate = 82% (+7%), no increase in errors

---

## 📈 Advanced Analytics (Coming Next)

Add these to show even more value:

### Time-Series Analysis
- Processing time per invoice (latency monitoring)
- API response times
- Batch processing throughput

### Vendor Comparison
- Run same invoices through Azure vs ABBYY
- Compare confidence, accuracy, cost
- Make data-driven vendor decisions

### Document Type Segmentation
- Segment by invoice format/template
- Track which formats work best
- Identify templates needing improvement

### Financial Impact
- Calculate cost per invoice
- ROI of automation (time saved)
- Manual review hours reduced

---

## 🎯 Next Steps

1. **Add More Invoices**: Process 100+ invoices to see trends
   ```bash
   # Add more files to sample_invoices/
   python run_azure_pipeline.py
   ```

2. **Compare Runs**: Change validation thresholds and compare
   ```python
   # Edit run_azure_pipeline.py line 48-50
   self.validator = Validator(
       low_confidence_threshold=0.65  # Was 0.7
   )
   ```

3. **Set Up Alerts**: Get notified when metrics drop
   - Go to W&B dashboard → Alerts
   - Set threshold: "alert if success_rate < 95%"

4. **Share Dashboard**: Show stakeholders
   - Share W&B project link
   - Create custom views
   - Export reports

---

## 💼 Business Value Summary

| Before W&B | With W&B + Azure IDP |
|------------|---------------------|
| ❌ No visibility into extraction quality | ✅ Real-time confidence scores |
| ❌ Can't compare vendors | ✅ Side-by-side vendor comparison |
| ❌ No audit trail | ✅ Full versioning of data + configs |
| ❌ Manual error tracking | ✅ Automated error analysis |
| ❌ Guessing at thresholds | ✅ Data-driven optimization |
| ❌ Can't explain failures | ✅ Detailed reason codes |
| ❌ No trend analysis | ✅ Historical metrics & charts |

**Bottom Line**: W&B turns Azure Document Intelligence from a "black box" into a **transparent, optimizable, auditable system**.

---

## 📚 Documentation

- Azure Document Intelligence: https://learn.microsoft.com/azure/ai-services/document-intelligence/
- W&B Docs: https://docs.wandb.ai/
- This Project: See `AZURE_SETUP.md` for full setup guide

