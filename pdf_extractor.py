"""
PDF Document Extractor for reconEngine
=======================================
Intelligently extracts data from:
- Bank Statements
- Invoices

Uses pdfplumber for table extraction with heuristic detection.
"""
from typing import Optional, Dict, Any, Tuple
import pdfplumber
import pandas as pd
import re
import pypdfium2 as pdfium  # PDFium renderer for the OCR fallback
import pytesseract

# Configure Tesseract path
import os
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


class PDFExtractionError(Exception):
    """Raised when PDF extraction fails."""
    pass


def detect_document_type(text_sample: str, df_sample: pd.DataFrame) -> str:
    """
    Heuristically detect whether a PDF is a bank statement or invoice.
    
    Returns: 'bank_statement', 'invoice', or 'unknown'
    
    Detection priority:
    1. Column names (strongest signal)
    2. Amount sign pattern (bank=mostly negative, invoice=mostly positive)
    3. Keyword search in raw text + cell values (weakest signal, PDFs often corrupt text)
    """
    cols_lower = [str(c).lower() for c in df_sample.columns]
    
    # ---- 1. Column name signals (strongest) ----
    bank_col_signals = ['debit', 'credit', 'balance', 'transaction', 'custody', 'withdrawal', 'deposit', 'opening', 'closing']
    invoice_col_signals = ['invoice', 'vendor', 'supplier', 'due', 'qty', 'quantity', 'rate', 'unit price', 'remit', 'po number', 'purchase order', 'tax', 'vat']
    
    bank_col_score = sum(1 for c in cols_lower if any(bk in c for bk in bank_col_signals)) * 3
    invoice_col_score = sum(1 for c in cols_lower if any(ik in c for ik in invoice_col_signals)) * 3
    
    # ---- 2. Amount sign pattern (strong) ----
    if 'amount' in cols_lower:
        try:
            amts = pd.to_numeric(df_sample['amount'], errors='coerce').dropna()
            if len(amts) >= 3:
                negative_ratio = (amts < 0).mean()
                positive_ratio = (amts > 0).mean()
                if negative_ratio > 0.6:
                    bank_col_score += 5  # Strong bank signal
                elif positive_ratio > 0.8:
                    invoice_col_score += 5  # Strong invoice signal
        except Exception:
            pass
    
    # ---- 3. Keyword search (weakest - PDF text extraction is often corrupted) ----
    df_text = " ".join(str(v) for v in df_sample.values.flatten() if pd.notna(v))
    combined_text = (text_sample + " " + df_text).lower()
    
    bank_keywords = [
        'statement', 'account', 'transaction', 'debit', 'credit',
        'balance', 'withdrawal', 'deposit', 'bank', 'opening balance',
        'closing balance', 'transaction date', 'available balance', 
        'ledger balance', 'custody', 'prime brokerage',
        'service charge', 'wire transfer', 'swift', 'fee',
        'current balance', 'previous balance'
    ]
    
    invoice_keywords = [
        'invoice', 'bill', 'vendor', 'supplier', 'due date',
        'invoice number', 'invoice date', 'bill to', 'ship to',
        'payment terms', 'subtotal', 'total due', 'remit', 'remittance',
        'accounts payable', 'qty', 'quantity', 'rate', 'unit price',
        'po number', 'purchase order', 'tax invoice', 'vat'
    ]
    
    bank_score = sum(1 for kw in bank_keywords if kw in combined_text)
    invoice_score = sum(1 for kw in invoice_keywords if kw in combined_text)
    
    # ---- Combine scores ----
    total_bank = bank_col_score + bank_score
    total_invoice = invoice_col_score + invoice_score
    
    if total_bank > total_invoice:
        return 'bank_statement'
    elif total_invoice > total_bank:
        return 'invoice'
    else:
        # Ultimate fallback: infer from amount signs alone
        if 'amount' in cols_lower:
            try:
                amts = pd.to_numeric(df_sample['amount'], errors='coerce').dropna()
                if len(amts) >= 3:
                    negative_ratio = (amts < 0).mean()
                    positive_ratio = (amts > 0).mean()
                    if negative_ratio > 0.4:
                        return 'bank_statement'
                    elif positive_ratio > 0.7:
                        return 'invoice'
            except Exception:
                pass
        return 'unknown'


def extract_tables_from_pdf(file_path: str) -> Tuple[pd.DataFrame, str]:
    """
    Extract tables from a PDF file.
    
    Returns:
        (DataFrame, document_type) where document_type is 'bank_statement', 'invoice', or 'unknown'
    """
    all_tables = []
    text_sample = ""
    
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Extract text for detection
            page_text = page.extract_text() or ""
            text_sample += page_text + " "
            
            # Extract tables
            tables = page.extract_tables()
            for table in tables:
                if table and len(table) > 0:
                    # Convert to DataFrame
                    df = pd.DataFrame(table[1:], columns=table[0])
                    df['_page'] = page_num + 1
                    all_tables.append(df)
    
    if not all_tables:
        # Try OCR fallback for scanned/image-based PDFs
        return _extract_tables_with_ocr(file_path)
    
    # Combine all tables — deduplicate column names first to avoid pd.concat crash
    seen = {}
    for i, df in enumerate(all_tables):
        new_cols = []
        for col in df.columns:
            col_str = str(col)
            if col_str in seen:
                seen[col_str] += 1
                new_cols.append(f"{col_str}_{seen[col_str]}")
            else:
                seen[col_str] = 0
                new_cols.append(col_str)
        df.columns = new_cols
    combined_df = pd.concat(all_tables, ignore_index=True)
    
    # Detect document type
    doc_type = detect_document_type(text_sample, combined_df)
    
    return combined_df, doc_type


def _extract_tables_with_ocr(file_path: str) -> Tuple[pd.DataFrame, str]:
    """
    OCR fallback for scanned/image-based PDFs.
    
    Uses PDFium (via pypdfium2) to render pages as images, then Tesseract
    to extract text.
    
    pypdfium2 is used rather than PyMuPDF because PyMuPDF is AGPL-3.0, and
    this project is published under the MIT licence. See ADR-014 in the
    hermes-os specification repository.
    """
    try:
        doc = pdfium.PdfDocument(file_path)
        all_text = ""
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Render at 2x scale (~144 DPI on A4) for good OCR quality.
            # The previous PyMuPDF implementation used a 2x matrix, which
            # produced the same effective resolution.
            bitmap = page.render(scale=2.0)
            img = bitmap.to_pil().convert("RGB")
            
            # Run OCR
            page_text = pytesseract.image_to_string(img)
            all_text += page_text + "\n"
        
        doc.close()
        
        if not all_text.strip():
            raise PDFExtractionError("OCR produced no text. The PDF may be password-protected or contain only images.")
        
        # Parse OCR text into a table structure
        df = _parse_ocr_text_to_table(all_text)
        
        if df.empty:
            raise PDFExtractionError("OCR extracted text but no structured data found. The document may not be a standard bank statement or invoice.")
        
        # Detect document type from OCR text
        doc_type = detect_document_type(all_text, df)
        
        return df, doc_type
        
    except PDFExtractionError:
        raise
    except Exception as e:
        raise PDFExtractionError(f"OCR failed: {str(e)}")


def _parse_ocr_text_to_table(text: str) -> pd.DataFrame:
    """
    Parse OCR-extracted text into a structured DataFrame.
    
    Attempts to identify and extract rows with dates, descriptions, and amounts.
    """
    import re
    
    rows = []
    lines = text.split('\n')
    
    # Patterns for detection
    date_pattern = re.compile(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}', re.IGNORECASE)
    amount_pattern = re.compile(r'\(?[\d,]+\.?\d*\)?|\d+\.\d{2}')
    
    # Header keywords to skip
    header_keywords = ['date', 'description', 'amount', 'debit', 'credit', 'balance', 'particulars', 'details', 'narrative']
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip lines that look like headers
        line_lower = line.lower()
        if any(kw in line_lower for kw in header_keywords):
            continue
        
        # Try to extract date
        date_match = date_pattern.search(line)
        date_str = date_match.group() if date_match else ""
        
        # Try to extract amounts (usually at the end of the line)
        amounts = amount_pattern.findall(line)
        amount = ""
        if amounts:
            # Last amount is usually the transaction amount
            amount = amounts[-1].replace(',', '').replace('(', '-').replace(')', '')
            try:
                amount = float(amount)
            except ValueError:
                amount = ""
        
        # Handle OCR cases where negative sign is separated from amount
        # e.g., "Test Vendor - 1000.00" should become -1000.00
        if amount != "" and amount > 0:
            # Check if the line ends with "-" before the amount
            line_before_amount = line[:line.rfind(amounts[-1])].strip()
            if line_before_amount.endswith('-'):
                amount = -amount
        
        # Description is the line without date and amount
        desc = line
        if date_str:
            desc = desc.replace(date_str, "")
        if amount != "":
            # Remove the amount from description
            for amt in amounts:
                desc = desc.replace(amt, "")
        desc = desc.strip()
        # Clean up trailing " -" from OCR
        desc = re.sub(r'\s+-\s*$', '', desc).strip()
        
        # Only add rows that have at least a description and some numeric value
        if desc and amount != "":
            rows.append({
                'date': date_str,
                'description': desc,
                'amount': amount
            })
    
    if not rows:
        return pd.DataFrame()
    
    df = pd.DataFrame(rows)
    df['_page'] = 1  # OCR doesn't track pages well
    return df


def clean_extracted_df(df: pd.DataFrame, doc_type: str) -> pd.DataFrame:
    """
    Clean and normalize extracted PDF data.
    
    - Remove empty rows/columns
    - Normalize column names
    - Parse amounts
    - Parse dates
    """
    # Drop completely empty columns
    df = df.dropna(axis=1, how='all')
    # Drop completely empty rows
    df = df.dropna(axis=0, how='all')
    
    # Strip whitespace from all string cells
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
    
    # Normalize column names (use substring matching for PDF-extracted names like "Debit (USD)")
    col_map = {}
    cols_lower = {c: c.lower().strip() for c in df.columns}
    
    # Priority: date > description > debit > credit > amount > invoice_number
    # Don't map both "Amount (ZAR)" and "Balance" to "amount" — keep only the first match
    used_targets = set()
    
    for orig_col, low_col in cols_lower.items():
        # Date columns
        if any(kw in low_col for kw in ('date', 'txn date', 'posted date', 'transaction date', 'invoice date', 'due date')):
            if 'date' not in used_targets:
                col_map[orig_col] = 'date'
                used_targets.add('date')
        # Description columns
        elif any(kw in low_col for kw in ('description', 'desc', 'particulars', 'details', 'narrative', 'memo', 'payee', 'vendor', 'supplier')):
            if 'description' not in used_targets:
                col_map[orig_col] = 'description'
                used_targets.add('description')
        # Debit column (outflows)
        elif 'debit' in low_col:
            if 'debit' not in used_targets:
                col_map[orig_col] = 'debit'
                used_targets.add('debit')
        # Credit column (inflows)
        elif 'credit' in low_col:
            if 'credit' not in used_targets:
                col_map[orig_col] = 'credit'
                used_targets.add('credit')
        # Amount column (only if no separate debit/credit, and not "balance")
        # Use word-boundary matching to avoid false positives (e.g. 'tax' matching 'amt' in 'tax amount')
        elif any(re.search(r'\b' + kw + r'\b', low_col) for kw in ('amount', 'amt', 'value', 'total', 'debit', 'credit', 'paid', 'payable')):
            if 'amount' not in used_targets:
                col_map[orig_col] = 'amount'
                used_targets.add('amount')
        # Balance — DON'T map to amount (it's a running total, not a transaction value)
        # Invoice number
        elif any(kw in low_col for kw in ('invoice number', 'inv #', 'invoice no', 'inv no')):
            if 'invoice_number' not in used_targets:
                col_map[orig_col] = 'invoice_number'
                used_targets.add('invoice_number')
    
    df = df.rename(columns=col_map)
    
    # If we have separate debit/credit columns, combine them into signed amounts
    # Debit = money going OUT (negative), Credit = money coming IN (positive)
    if 'debit' in df.columns and 'credit' in df.columns:
        # Parse to numeric first (they may still be strings like "4,500.00")
        df['debit_parsed'] = pd.to_numeric(df['debit'].astype(str).str.replace(',', '').str.replace('R', '').str.replace('$', '').replace(['nan', 'None', ''], pd.NA), errors='coerce')
        df['credit_parsed'] = pd.to_numeric(df['credit'].astype(str).str.replace(',', '').str.replace('R', '').str.replace('$', '').replace(['nan', 'None', ''], pd.NA), errors='coerce')
        df['amount'] = df['credit_parsed'].fillna(0) - df['debit_parsed'].fillna(0)
        df = df.drop(columns=['debit', 'credit', 'debit_parsed', 'credit_parsed'], errors='ignore')
    elif 'debit' in df.columns and 'amount' not in df.columns:
        df['debit_parsed'] = pd.to_numeric(df['debit'].astype(str).str.replace(',', '').str.replace('R', '').str.replace('$', '').replace(['nan', 'None', ''], pd.NA), errors='coerce')
        df['amount'] = -df['debit_parsed'].fillna(0).abs()
        df = df.drop(columns=['debit', 'debit_parsed'], errors='ignore')
    elif 'credit' in df.columns and 'amount' not in df.columns:
        df['credit_parsed'] = pd.to_numeric(df['credit'].astype(str).str.replace(',', '').str.replace('R', '').str.replace('$', '').replace(['nan', 'None', ''], pd.NA), errors='coerce')
        df['amount'] = df['credit_parsed'].fillna(0)
        df = df.drop(columns=['credit', 'credit_parsed'], errors='ignore')
    elif 'amount' in df.columns:
        # amount column exists but might be a running balance — negate it for bank statements
        # (positive debits in bank statements represent outflows)
        pass
    
    # Parse amount column
    if 'amount' in df.columns:
        df['amount'] = df['amount'].apply(_parse_amount)
    
    # Parse date column
    if 'date' in df.columns:
        df['date'] = df['date'].apply(_parse_date)
    
    # Drop rows without essential data
    if 'description' in df.columns:
        df = df[df['description'].notna() & (df['description'] != '')]
    if 'amount' in df.columns:
        df = df[df['amount'].notna()]
    
    return df


def _parse_amount(val) -> Optional[float]:
    """Parse amount from various formats."""
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    
    s = str(val).strip()
    # Remove currency symbols, commas, parentheses
    s = s.replace('R', '').replace('$', '').replace('GBP', '').replace('EUR', '')
    s = s.replace(',', '')
    if s.startswith('(') and s.endswith(')'):
        s = '-' + s[1:-1]
    
    try:
        return float(s)
    except ValueError:
        return None


def _parse_date(val) -> Optional[str]:
    """Parse date to ISO format string."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    
    # Try common formats
    formats = [
        '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y',
        '%Y/%m/%d', '%d.%m.%Y', '%m.%d.%Y', '%B %d, %Y', '%b %d, %Y'
    ]
    
    for fmt in formats:
        try:
            dt = pd.to_datetime(s, format=fmt)
            return dt.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            continue
    
    # Fallback to pandas auto-parse
    try:
        dt = pd.to_datetime(s, dayfirst=True)
        return dt.strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        return None


def process_pdf(file_path: str) -> Dict[str, Any]:
    """
    Main entry point for PDF processing.
    
    Returns:
        {
            'success': bool,
            'doc_type': str,
            'data': pd.DataFrame,
            'message': str
        }
    """
    try:
        df, doc_type = extract_tables_from_pdf(file_path)
        df = clean_extracted_df(df, doc_type)
        
        if df.empty:
            return {
                'success': False,
                'doc_type': doc_type,
                'data': None,
                'message': f"Extracted PDF as {doc_type}, but no valid data rows found after cleaning. Check that the PDF contains readable tables."
            }
        
        return {
            'success': True,
            'doc_type': doc_type,
            'data': df,
            'message': f"Successfully extracted {doc_type} with {len(df)} rows."
        }
    
    except PDFExtractionError as e:
        return {
            'success': False,
            'doc_type': 'unknown',
            'data': None,
            'message': f"PDF extraction failed: {str(e)}"
        }
    except Exception as e:
        return {
            'success': False,
            'doc_type': 'unknown',
            'data': None,
            'message': f"Unexpected error: {str(e)}"
        }
