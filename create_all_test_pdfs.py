#!/usr/bin/env python3
"""
Generate PDF versions of all test CSV files.
"""
import csv
import os
from fpdf import FPDF

TEST_DIR = os.path.join(os.path.dirname(__file__), "test_data")

def csv_to_pdf(csv_path, pdf_path):
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 9)
    
    # Headers
    col_w = 190 / len(headers) if headers else 40
    for h in headers:
        pdf.cell(col_w, 10, str(h), border=1)
    pdf.ln()
    
    # Rows
    pdf.set_font("Helvetica", "", 8)
    for row in rows:
        for cell in row:
            pdf.cell(col_w, 10, str(cell), border=1)
        pdf.ln()
    
    pdf.output(pdf_path)
    print(f"Created: {os.path.basename(pdf_path)} ({len(rows)} rows)")

if __name__ == "__main__":
    for i in range(1, 5):
        for kind in ['bank_statement', 'invoices']:
            csv_path = os.path.join(TEST_DIR, f"company{i}_{kind}.csv")
            pdf_path = os.path.join(TEST_DIR, f"company{i}_{kind}.pdf")
            if os.path.exists(csv_path):
                csv_to_pdf(csv_path, pdf_path)
    
    print("\nDone!")
