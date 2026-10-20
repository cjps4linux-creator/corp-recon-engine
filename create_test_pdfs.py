"""
Generate a simple PDF from CSV data for testing PDF extraction.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fpdf import FPDF
import csv

def csv_to_pdf(csv_path, pdf_path):
    """Convert a CSV file to a simple tabular PDF."""
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 10)
    
    # Headers
    for h in headers:
        pdf.cell(40, 10, h, border=1)
    pdf.ln()
    
    # Rows
    pdf.set_font("Helvetica", "", 9)
    for row in rows:
        for cell in row:
            pdf.cell(40, 10, str(cell), border=1)
        pdf.ln()
    
    pdf.output(pdf_path)
    print(f"Created: {pdf_path}")

if __name__ == "__main__":
    base = os.path.join(os.path.dirname(__file__), "test_data")
    csv_to_pdf(os.path.join(base, "company1_bank_statement.csv"), os.path.join(base, "company1_bank_statement.pdf"))
    csv_to_pdf(os.path.join(base, "company1_invoices.csv"), os.path.join(base, "company1_invoices.pdf"))
