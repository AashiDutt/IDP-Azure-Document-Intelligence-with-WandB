"""
Enhanced visualizations that show what Azure actually extracted
This makes the dashboard useful even with imperfect test data
"""
import wandb
import pandas as pd


def log_azure_extraction_insights(df, all_results):
    """
    Log visualizations based on what Azure actually extracted,
    not just our business logic.
    """
    print("\n  === Enhanced Azure Extraction Visualizations ===")
    
    # 1. FIELD EXTRACTION SUCCESS RATES
    # Show which fields Azure successfully extracted
    field_success_data = []
    fields_to_check = ["invoice_number", "supplier_name", "total", "invoice_date"]
    
    for field in fields_to_check:
        if field in df.columns:
            success_count = df[field].notna().sum()
            total_count = len(df)
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0
            field_success_data.append([field, success_rate])
    
    if field_success_data:
        field_table = wandb.Table(
            data=field_success_data,
            columns=["field", "extraction_success_rate"]
        )
        wandb.log({
            "azure_field_extraction_rates": wandb.plot.bar(
                field_table,
                "field",
                "extraction_success_rate",
                title="Azure Field Extraction Success Rate (%)"
            )
        })
        print("  * Logged field extraction rates")
    
    # 2. CONFIDENCE SCORE HEATMAP
    # Show confidence scores for each invoice and field
    confidence_data = []
    for idx, row in df.iterrows():
        if row.get("status") == "success":
            confidence_data.append([
                row.get("doc_id", "Unknown"),
                "Invoice Number",
                row.get("conf_invoice_number", 0) * 100
            ])
            confidence_data.append([
                row.get("doc_id", "Unknown"),
                "Total Amount",
                row.get("conf_total", 0) * 100
            ])
    
    if confidence_data:
        conf_heatmap_table = wandb.Table(
            data=confidence_data,
            columns=["document", "field", "confidence"]
        )
        wandb.log({"confidence_heatmap": conf_heatmap_table})
        print("  * Logged confidence heatmap")
    
    # 3. EXTRACTED VS MISSING FIELDS
    # Show what was successfully extracted vs what's missing
    success_count = df[df["status"] == "success"]["invoice_number"].notna().sum()
    missing_count = len(df) - success_count
    
    extraction_data = [
        ["Extracted", success_count],
        ["Missing", missing_count]
    ]
    extraction_table = wandb.Table(data=extraction_data, columns=["status", "count"])
    wandb.log({
        "invoice_number_extraction": wandb.plot.bar(
            extraction_table,
            "status",
            "count",
            title="Invoice Number: Extracted vs Missing"
        )
    })
    print("  * Logged extraction completeness")
    
    # 4. ACTUAL TEXT EXTRACTED
    # Show what Azure actually found
    extracted_suppliers = df[df["status"] == "success"]["supplier_name"].dropna().unique()
    extracted_numbers = df[df["status"] == "success"]["invoice_number"].dropna().unique()
    
    wandb.log({
        "unique_suppliers_found": len(extracted_suppliers),
        "unique_invoice_numbers_found": len(extracted_numbers),
        "suppliers_list": list(extracted_suppliers)[:10],  # First 10
        "invoice_numbers_list": list(extracted_numbers)[:10]
    })
    print(f"  * Found {len(extracted_suppliers)} unique suppliers")
    print(f"  * Found {len(extracted_numbers)} unique invoice numbers")
    
    # 5. DOCUMENT COMPARISON
    # Compare documents side by side
    comparison_data = []
    for idx, row in df.iterrows():
        if row.get("status") == "success":
            comparison_data.append([
                row.get("doc_id", "Unknown"),
                row.get("supplier_name", "N/A"),
                row.get("invoice_number", "N/A"),
                row.get("total", 0),
                row.get("conf_total", 0) * 100,
                row.get("category", "Unknown")
            ])
    
    if comparison_data:
        comparison_table = wandb.Table(
            data=comparison_data,
            columns=["Document", "Supplier", "Invoice#", "Amount", "Confidence%", "Category"]
        )
        wandb.log({"document_comparison": comparison_table})
        print("  * Logged document comparison table")
    
    # 6. CATEGORIZATION INSIGHTS
    # Show how documents were categorized
    if "category" in df.columns:
        category_breakdown = df["category"].value_counts()
        print(f"\n  Categories detected:")
        for cat, count in category_breakdown.items():
            print(f"    - {cat}: {count}")
    
    # 7. WHAT'S MISSING (Most Important for Debugging)
    missing_analysis = {
        "invoices_missing_total": (df["total"].isna() | (df["total"] == 0)).sum(),
        "invoices_missing_date": df["invoice_date"].isna().sum() if "invoice_date" in df.columns else 0,
        "invoices_missing_supplier": df["supplier_name"].isna().sum() if "supplier_name" in df.columns else 0,
    }
    
    wandb.log(missing_analysis)
    
    print(f"\n  WARNING: Missing Data Summary:")
    print(f"    - {missing_analysis['invoices_missing_total']} invoices missing total")
    print(f"    - {missing_analysis['invoices_missing_date']} invoices missing date")
    print(f"    - {missing_analysis['invoices_missing_supplier']} invoices missing supplier")

