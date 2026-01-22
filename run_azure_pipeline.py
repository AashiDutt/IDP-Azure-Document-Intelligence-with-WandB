"""
Run invoice processing pipeline with Azure Document Intelligence + W&B observability.

This script:
1. Uses Azure Document Intelligence for extraction
2. Normalizes to canonical schema
3. Applies validation and routing
4. Logs everything to W&B as JSON with full observability
"""
import os
import sys
import json
from typing import Dict
from datetime import datetime
from dotenv import load_dotenv
from azure_adapter import AzureDocumentIntelligenceAdapter
from normalizer import Normalizer
from validator import Validator
from business_analyzer import BusinessAnalyzer
from enhanced_visualizations import log_azure_extraction_insights
import wandb
import pandas as pd

# Load environment variables from .env file
load_dotenv()


class AzurePipeline:
    """
    Pipeline for Azure Document Intelligence -> Canonical Schema -> W&B
    """
    
    def __init__(self, azure_endpoint: str, azure_key: str, wandb_project: str = "invoice-azure-wandb"):
        """
        Initialize pipeline.
        
        Args:
            azure_endpoint: Azure endpoint URL
            azure_key: Azure API key
            wandb_project: W&B project name
        """
        print("\n" + "="*70)
        print("Invoice Processing Pipeline: Azure Document Intelligence + W&B")
        print("="*70)
        
        # Initialize Azure adapter
        self.azure_adapter = AzureDocumentIntelligenceAdapter(
            endpoint=azure_endpoint,
            api_key=azure_key,
            model_id="prebuilt-invoice"
        )
        print("Azure Document Intelligence: Connected")
        
        # Initialize normalizer, validator, and business analyzer
        self.normalizer = Normalizer(pipeline_version="1.0.0")
        self.validator = Validator(
            low_confidence_threshold=0.7,
            high_total_threshold=100000.0,
            currency_tolerance={"USD": 0.01, "EUR": 0.01, "GBP": 0.01}
        )
        self.business_analyzer = BusinessAnalyzer()
        print("Validator: Ready")
        print("Business Analyzer: Ready")
        
        # Initialize W&B
        self.wandb_project = wandb_project
        wandb.init(
            project=wandb_project,
            config={
                "vendor": "azure_document_intelligence",
                "model": "prebuilt-invoice",
                "pipeline_version": "1.0.0",
                "low_confidence_threshold": 0.7,
                "high_total_threshold": 100000.0
            }
        )
        print(f"W&B: Connected to project '{wandb_project}'")
        print("="*70 + "\n")
    
    def process_invoice(self, file_path_or_url: str, doc_id: str = None) -> Dict:
        """
        Process a single invoice through the complete pipeline.
        
        Args:
            file_path_or_url: Path to invoice file or URL
            doc_id: Document identifier (auto-generated if not provided)
            
        Returns:
            Dictionary with all results including JSON output
        """
        # Generate doc_id if needed
        if doc_id is None:
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            doc_id = f"INV-{timestamp}"
        
        print(f"\n{'='*70}")
        print(f"Processing: {doc_id}")
        print(f"{'='*70}")
        
        # Step 1: Extract with Azure
        print("\n[1/4] Azure Document Intelligence Extraction")
        raw_output = self.azure_adapter.extract_invoice(file_path_or_url, doc_id)
        
        # Step 2: Normalize to canonical schema
        print("\n[2/4] Normalization to Canonical Schema")
        normalized = self.normalizer.normalize(
            raw_output,
            "azure_document_intelligence",
            "prebuilt-invoice"
        )
        print(f"  * Normalized to canonical schema")
        print(f"  - Invoice #: {normalized.invoice_number.value if normalized.invoice_number else 'N/A'}")
        print(f"  - Supplier: {normalized.supplier_name.value if normalized.supplier_name else 'N/A'}")
        total_val = normalized.total.value if normalized.total else 0
        total_conf = normalized.total.confidence if normalized.total else 0
        print(f"  - Total: ${float(total_val) if total_val else 0:.2f}")
        print(f"  - Confidence: {total_conf:.2%}")
        
        # Step 3: Validate
        print("\n[3/4] Validation")
        validation = self.validator.validate(normalized)
        if validation.passed:
            print(f"  * Validation PASSED")
        else:
            print(f"  * Validation FAILED")
            for error in validation.errors:
                print(f"    • {error}")
        
        # Step 4: Route
        print("\n[4/4] Routing Decision")
        routing = self.validator.route(normalized, validation)
        print(f"  - Outcome: {routing.outcome}")
        print(f"  - Confidence: {routing.confidence_score:.2%}")
        if routing.reason_codes:
            print(f"  - Reasons: {', '.join(routing.reason_codes)}")
        
        # Step 5: Business Analysis
        print("\n[5/5] Business Analysis")
        business_insights = self.business_analyzer.analyze_invoice(
            {
                "total": normalized.total.value if normalized.total else None,
                "supplier_name": normalized.supplier_name.value if normalized.supplier_name else None,
                "invoice_number": normalized.invoice_number.value if normalized.invoice_number else None,
                "invoice_date": normalized.invoice_date.value if normalized.invoice_date else None,
                "validation_passed": validation.passed,
                "confidence_scores": {
                    "total": normalized.total.confidence if normalized.total else 0,
                    "invoice_number": normalized.invoice_number.confidence if normalized.invoice_number else 0
                }
            },
            raw_output
        )
        print(f"  - Category: {business_insights['category']}")
        print(f"  - Priority: {business_insights['priority']}")
        print(f"  - Risk Level: {business_insights['risk_level']}")
        print(f"  - Processing Cost: ${business_insights['processing_cost']:.4f}")
        
        print(f"\n{'='*70}\n")
        
        # Convert to JSON for output
        result_json = {
            "doc_id": doc_id,
            "extraction": {
                "vendor": "azure_document_intelligence",
                "timestamp": raw_output["extraction_metadata"]["timestamp"],
                "fields": raw_output["fields"],
                "line_items": raw_output["line_items"]
            },
            "normalized": {
                "invoice_number": normalized.invoice_number.value if normalized.invoice_number else None,
                "invoice_date": normalized.invoice_date.value if normalized.invoice_date else None,
                "supplier_name": normalized.supplier_name.value if normalized.supplier_name else None,
                "supplier_id": normalized.supplier_id.value if normalized.supplier_id else None,
                "currency": normalized.currency.value if normalized.currency else None,
                "subtotal": normalized.subtotal.value if normalized.subtotal else None,
                "tax": normalized.tax.value if normalized.tax else None,
                "total": normalized.total.value if normalized.total else None,
                "po_number": normalized.po_number.value if normalized.po_number else None,
                "confidence_scores": {
                    "invoice_number": normalized.invoice_number.confidence if normalized.invoice_number else 0,
                    "total": normalized.total.confidence if normalized.total else 0,
                    "supplier": normalized.supplier_name.confidence if normalized.supplier_name else 0
                }
            },
            "validation": {
                "passed": validation.passed,
                "checks": validation.checks,
                "errors": validation.errors,
                "warnings": validation.warnings
            },
            "routing": {
                "outcome": routing.outcome,
                "confidence": routing.confidence_score,
                "reason_codes": routing.reason_codes
            }
        }
        
        return {
            "doc_id": doc_id,
            "normalized": normalized,
            "validation": validation,
            "routing": routing,
            "raw_output": raw_output,
            "business_insights": business_insights,
            "json_output": result_json
        }
    
    def process_batch(self, invoices: list, output_file: str = "results.json"):
        """
        Process multiple invoices and log to W&B.
        
        Args:
            invoices: List of file paths or URLs
            output_file: Path to save JSON results
            
        Returns:
            List of all results
        """
        print(f"\n{'='*70}")
        print(f"BATCH PROCESSING: {len(invoices)} invoices")
        print(f"{'='*70}\n")
        
        all_results = []
        table_rows = []
        
        for i, invoice_path in enumerate(invoices, 1):
            print(f"\n[{i}/{len(invoices)}] ", end="")
            
            # Determine doc_id
            if invoice_path.startswith(('http://', 'https://')):
                doc_id = f"DOC-URL-{i:03d}"
            else:
                doc_id = f"DOC-{os.path.splitext(os.path.basename(invoice_path))[0]}"
            
            try:
                result = self.process_invoice(invoice_path, doc_id)
                all_results.append(result["json_output"])
                
                # Build table row
                normalized = result["normalized"]
                routing = result["routing"]
                insights = result["business_insights"]
                
                table_rows.append({
                    "doc_id": doc_id,
                    "invoice_number": normalized.invoice_number.value if normalized.invoice_number else None,
                    "supplier_name": normalized.supplier_name.value if normalized.supplier_name else None,
                    "total": normalized.total.value if normalized.total else None,
                    "conf_total": normalized.total.confidence if normalized.total else None,
                    "conf_invoice_number": normalized.invoice_number.confidence if normalized.invoice_number else None,
                    "validation_passed": result["validation"].passed,
                    "routing_outcome": routing.outcome,
                    "routing_confidence": routing.confidence_score,
                    "reason_codes": ", ".join(routing.reason_codes) if routing.reason_codes else None,
                    "needs_review": routing.outcome == "NEEDS_REVIEW",
                    "has_reconciliation_error": "TOTAL_MISMATCH" in routing.reason_codes,
                    "has_low_confidence": "LOW_CONFIDENCE" in routing.reason_codes,
                    # Business insights
                    "category": insights["category"],
                    "priority": insights["priority"],
                    "urgency": insights["urgency"],
                    "risk_level": insights["risk_level"],
                    "processing_cost": insights["processing_cost"],
                    "document_quality": insights["document_quality"],
                    "status": "success"
                })
                
            except Exception as e:
                print(f"ERROR: {e}")
                all_results.append({
                    "doc_id": doc_id,
                    "status": "error",
                    "error": str(e)
                })
                table_rows.append({
                    "doc_id": doc_id,
                    "status": "error",
                    "error_message": str(e)
                })
        
        # Save JSON output
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\n* Saved results to {output_file}")
        
        # Log to W&B
        self._log_to_wandb(table_rows, output_file)
        
        return all_results
    
    def _log_to_wandb(self, table_rows: list, json_file: str, all_results: list = None):
        """Log comprehensive results to W&B with useful visualizations."""
        print(f"\n{'='*70}")
        print("Logging to W&B")
        print(f"{'='*70}")
        
        # Create DataFrame and table
        df = pd.DataFrame(table_rows)
        
        # Main results table
        table = wandb.Table(dataframe=df)
        wandb.log({"invoice_results_table": table})
        print("  * Logged results table")
        
        # Log JSON file as artifact
        artifact = wandb.Artifact("invoice_results", type="dataset")
        artifact.add_file(json_file)
        wandb.log_artifact(artifact)
        print(f"  * Logged JSON artifact: {json_file}")
        
        # Filter successful extractions
        success_df = df[df["status"] == "success"]
        
        if len(success_df) > 0:
            # === CORE METRICS ===
            metrics = {
                "total_invoices": len(df),
                "successful_extractions": len(success_df),
                "failed_extractions": len(df) - len(success_df),
                "success_rate": len(success_df) / len(df),
                "auto_post_count": (success_df["routing_outcome"] == "AUTO_POST").sum(),
                "needs_review_count": success_df["needs_review"].sum(),
                "auto_post_rate": (success_df["routing_outcome"] == "AUTO_POST").mean(),
                "needs_review_rate": success_df["needs_review"].mean(),
                "validation_pass_rate": success_df["validation_passed"].mean(),
            }
            
            # === CONFIDENCE METRICS ===
            if "conf_total" in success_df.columns:
                metrics.update({
                    "avg_confidence_total": success_df["conf_total"].mean(),
                    "min_confidence_total": success_df["conf_total"].min(),
                    "max_confidence_total": success_df["conf_total"].max(),
                    "avg_confidence_invoice_num": success_df["conf_invoice_number"].mean(),
                    "low_confidence_count": (success_df["conf_total"] < 0.7).sum(),
                })
            
            # === FIELD EXTRACTION RATES ===
            field_extraction_rates = {
                "extraction_rate_invoice_number": success_df["invoice_number"].notna().mean(),
                "extraction_rate_supplier_name": success_df["supplier_name"].notna().mean(),
                "extraction_rate_total": success_df["total"].notna().mean(),
            }
            metrics.update(field_extraction_rates)
            
            # === ERROR ANALYSIS ===
            if "has_reconciliation_error" in success_df.columns:
                metrics["reconciliation_error_count"] = success_df["has_reconciliation_error"].sum()
                metrics["low_confidence_count"] = success_df["has_low_confidence"].sum()
            
            wandb.log(metrics)
            print("  * Logged core metrics")
            
            # === CONFIDENCE DISTRIBUTION HISTOGRAM ===
            if "conf_total" in success_df.columns and success_df["conf_total"].notna().any():
                conf_data = [[x] for x in success_df["conf_total"].dropna()]
                conf_table = wandb.Table(data=conf_data, columns=["confidence"])
                wandb.log({
                    "confidence_distribution": wandb.plot.histogram(
                        conf_table, 
                        "confidence",
                        title="Confidence Score Distribution (Total Field)"
                    )
                })
                print("  * Logged confidence distribution")
            
            # === ROUTING OUTCOME PIE CHART ===
            routing_counts = success_df["routing_outcome"].value_counts()
            routing_data = [[outcome, int(count)] for outcome, count in routing_counts.items()]
            routing_table = wandb.Table(data=routing_data, columns=["outcome", "count"])
            wandb.log({
                "routing_outcomes": wandb.plot.bar(
                    routing_table,
                    "outcome",
                    "count",
                    title="Routing Decisions: AUTO_POST vs NEEDS_REVIEW"
                )
            })
            print("  * Logged routing distribution")
            
            # === REASON CODES ANALYSIS ===
            reason_code_counts = {}
            for codes in success_df["reason_codes"].dropna():
                if codes:
                    for code in str(codes).split(", "):
                        reason_code_counts[code] = reason_code_counts.get(code, 0) + 1
            
            if reason_code_counts:
                reason_data = [[code, count] for code, count in sorted(reason_code_counts.items(), key=lambda x: x[1], reverse=True)]
                reason_table = wandb.Table(data=reason_data, columns=["reason_code", "count"])
                wandb.log({
                    "reason_codes_analysis": wandb.plot.bar(
                        reason_table,
                        "reason_code",
                        "count",
                        title="Top Reason Codes for Manual Review"
                    )
                })
                print("  * Logged reason codes analysis")
            
            # === FIELD-LEVEL CONFIDENCE COMPARISON ===
            if "conf_invoice_number" in success_df.columns:
                conf_comparison_data = [
                    ["Invoice Number", success_df["conf_invoice_number"].mean()],
                    ["Total", success_df["conf_total"].mean()],
                ]
                conf_comparison_table = wandb.Table(
                    data=conf_comparison_data,
                    columns=["field", "avg_confidence"]
                )
                wandb.log({
                    "field_confidence_comparison": wandb.plot.bar(
                        conf_comparison_table,
                        "field",
                        "avg_confidence",
                        title="Average Confidence by Field"
                    )
                })
                print("  * Logged field-level confidence comparison")
            
            # === VALIDATION CHECKS BREAKDOWN ===
            validation_checks = []
            for idx, row in success_df.iterrows():
                if row.get("validation_passed"):
                    validation_checks.append(["Passed", 1])
                else:
                    validation_checks.append(["Failed", 1])
            
            if validation_checks:
                val_table = wandb.Table(data=validation_checks, columns=["status", "count"])
                wandb.log({
                    "validation_results": wandb.plot.bar(
                        val_table,
                        "status",
                        "count",
                        title="Validation Pass/Fail"
                    )
                })
                print("  * Logged validation breakdown")
            
            # === SUCCESS vs FAILURE ===
            status_data = [
                ["Successful", len(success_df)],
                ["Failed", len(df) - len(success_df)]
            ]
            status_table = wandb.Table(data=status_data, columns=["status", "count"])
            wandb.log({
                "extraction_success_rate": wandb.plot.bar(
                    status_table,
                    "status",
                    "count",
                    title="Extraction Success vs Failure"
                )
            })
            print("  * Logged success/failure breakdown")
            
            # === BUSINESS INSIGHTS VISUALIZATIONS ===
            
            # 1. Document Categories Distribution
            if "category" in success_df.columns:
                category_counts = success_df["category"].value_counts()
                category_data = [[cat, int(count)] for cat, count in category_counts.items()]
                category_table = wandb.Table(data=category_data, columns=["category", "count"])
                wandb.log({
                    "document_categories": wandb.plot.bar(
                        category_table,
                        "category",
                        "count",
                        title="Invoice Categories Distribution"
                    )
                })
                print("  * Logged document categories")
            
            # 2. Total Cost by Category
            if "category" in success_df.columns and "total" in success_df.columns:
                category_totals = success_df.groupby("category")["total"].sum().reset_index()
                cost_by_category_data = [[row["category"], float(row["total"]) if row["total"] else 0] 
                                         for _, row in category_totals.iterrows()]
                cost_category_table = wandb.Table(data=cost_by_category_data, columns=["category", "total_amount"])
                wandb.log({
                    "cost_by_category": wandb.plot.bar(
                        cost_category_table,
                        "category",
                        "total_amount",
                        title="Total Cost by Category"
                    )
                })
                print("  * Logged cost by category")
            
            # 3. Priority Distribution
            if "priority" in success_df.columns:
                priority_counts = success_df["priority"].value_counts()
                priority_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
                priority_data = [[p, int(priority_counts.get(p, 0))] for p in priority_order if p in priority_counts]
                priority_table = wandb.Table(data=priority_data, columns=["priority", "count"])
                wandb.log({
                    "priority_distribution": wandb.plot.bar(
                        priority_table,
                        "priority",
                        "count",
                        title="Invoice Priority Levels"
                    )
                })
                print("  * Logged priority distribution")
            
            # 4. Risk Level Distribution
            if "risk_level" in success_df.columns:
                risk_counts = success_df["risk_level"].value_counts()
                risk_data = [[risk, int(count)] for risk, count in risk_counts.items()]
                risk_table = wandb.Table(data=risk_data, columns=["risk_level", "count"])
                wandb.log({
                    "risk_level_distribution": wandb.plot.bar(
                        risk_table,
                        "risk_level",
                        "count",
                        title="Risk Level Assessment"
                    )
                })
                print("  * Logged risk levels")
            
            # 5. Processing Cost Summary
            if "processing_cost" in success_df.columns:
                total_cost = success_df["processing_cost"].sum()
                avg_cost = success_df["processing_cost"].mean()
                wandb.log({
                    "total_processing_cost": total_cost,
                    "avg_processing_cost_per_invoice": avg_cost
                })
                print(f"  * Logged processing costs (Total: ${total_cost:.4f})")
            
            # 6. Document Quality Assessment
            if "document_quality" in success_df.columns:
                quality_counts = success_df["document_quality"].value_counts()
                quality_data = [[qual, int(count)] for qual, count in quality_counts.items()]
                quality_table = wandb.Table(data=quality_data, columns=["quality", "count"])
                wandb.log({
                    "document_quality": wandb.plot.bar(
                        quality_table,
                        "quality",
                        "count",
                        title="Document Quality Assessment"
                    )
                })
                print("  * Logged document quality")
            
            # 7. Top Suppliers by Volume
            if "supplier_name" in success_df.columns:
                supplier_counts = success_df["supplier_name"].value_counts().head(10)
                supplier_data = [[supp, int(count)] for supp, count in supplier_counts.items()]
                supplier_table = wandb.Table(data=supplier_data, columns=["supplier", "invoice_count"])
                wandb.log({
                    "top_suppliers": wandb.plot.bar(
                        supplier_table,
                        "supplier",
                        "invoice_count",
                        title="Top Suppliers by Volume"
                    )
                })
                print("  * Logged top suppliers")
            
            # 8. ENHANCED AZURE EXTRACTION INSIGHTS
            # Show what Azure actually extracted
            log_azure_extraction_insights(success_df, all_results)
        else:
            # Log failure metrics even if no successes
            wandb.log({
                "total_invoices": len(df),
                "successful_extractions": 0,
                "failed_extractions": len(df),
                "success_rate": 0.0
            })
            print("  WARNING: No successful extractions to analyze")
        
        print(f"{'='*70}\n")
    
    def finish(self):
        """Finish W&B run."""
        wandb.finish()
        print("* Pipeline completed. Check W&B dashboard!")


def main():
    """Run the pipeline."""
    
    # Azure credentials from environment variables
    AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
    AZURE_KEY = os.getenv("AZURE_KEY")
    
    # Validate credentials are set
    if not AZURE_ENDPOINT or not AZURE_KEY:
        print("\nERROR: Azure credentials not found!")
        print("\nPlease set environment variables:")
        print("  export AZURE_ENDPOINT='your-endpoint-here'")
        print("  export AZURE_KEY='your-api-key-here'")
        print("\nOr create a .env file (see .env.example)")
        sys.exit(1)
    
    # Initialize pipeline
    pipeline = AzurePipeline(
        azure_endpoint=AZURE_ENDPOINT,
        azure_key=AZURE_KEY,
        wandb_project="invoice-azure-wandb"
    )
    
    # Example invoices to process
    # You can use URLs or local file paths
    invoices = [
        # Sample invoice from Azure
        "https://raw.githubusercontent.com/Azure-Samples/cognitive-services-REST-api-samples/master/curl/form-recognizer/invoice_sample.jpg",
        
        # Add more URLs or local files here:
        # "sample_invoices/invoice_001.pdf",
        # "sample_invoices/invoice_002.pdf",
        # "https://example.com/another_invoice.pdf",
    ]
    
    # Check for local invoices directory
    if os.path.exists("sample_invoices"):
        local_invoices = [
            os.path.join("sample_invoices", f)
            for f in os.listdir("sample_invoices")
            if f.endswith(('.pdf', '.png', '.jpg', '.jpeg', '.tiff'))
        ]
        if local_invoices:
            print(f"Found {len(local_invoices)} local invoices")
            invoices.extend(local_invoices[:10])  # Add up to 10 local invoices
    
    # Process all invoices
    results = pipeline.process_batch(invoices, output_file="azure_results.json")
    
    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total processed: {len(results)}")
    
    success_count = sum(1 for r in results if r.get('status') != 'error')
    print(f"Successful: {success_count}")
    print(f"Failed: {len(results) - success_count}")
    
    auto_post = sum(1 for r in results if r.get('routing', {}).get('outcome') == 'AUTO_POST')
    print(f"\nRouting:")
    print(f"  AUTO_POST: {auto_post}")
    print(f"  NEEDS_REVIEW: {success_count - auto_post}")
    
    print("\n" + "="*70)
    print("* Results saved to: azure_results.json")
    print("* Check W&B dashboard for interactive analysis!")
    print("="*70 + "\n")
    
    # Finish
    pipeline.finish()


if __name__ == "__main__":
    main()

