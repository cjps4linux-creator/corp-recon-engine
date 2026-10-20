"""
ReconEngine Stress-Test Dataset Generator
==========================================
Generates a single-company test dataset with:
- 70+ realistic bank transactions
- 65+ realistic invoices
- Intentional real-world reconciliation issues:
  * Amount rounding differences (1-2 cents)
  * Date shifts (bank processes T+1)
  * Description variations (abbreviations, typos, suffixes)
  * Duplicate entries (double-charges, duplicate invoices)
  * Missing entries (unrecorded bank debits, unpaid invoices)
  * Partial payments
  * Refunds/credits
  * Currency mismatches (ZAR vs USD)
  * Tax/VAT discrepancies
  * Split payments across multiple bank rows
  * PDF extraction challenges (merged cells, multi-line headers)
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
from fpdf import FPDF

# ──────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────
random.seed(20260911)
OUTPUT_DIR = Path(__file__).parent / "stress_test_data"
OUTPUT_DIR.mkdir(exist_ok=True)

COMPANY = {
    "name": "Nexus Digital Solutions (Pty) Ltd",
    "reg": "2019/123456/07",
    "vat": "4123456789",
    "bank": "First National Bank",
    "account": "6210 1234 5678",
    "branch": "250655",
    "period": "January 2025",
    "opening_balance": 850_000.00,
    "closing_balance": 623_750.00,
}

# ──────────────────────────────────────────────────────
# Vendor master — with canonical + alias names
# ──────────────────────────────────────────────────────
VENDORS = [
    # (canonical, aliases_for_bank, aliases_for_invoice)
    ("Amazon Web Services", ["AWS Web Services", "Amazon Web Svc", "AWS *Web*", "AMAZON AWS"], ["AWS Web Services", "Amazon Web Services", "Amazon.com (AWS)"]),
    ("Google Workspace", ["Google *Workspace*", "Google Cloud", "Google G Suite", "Google LLC"], ["Google Workspace", "Google Cloud", "Alphabet / Google"]),
    ("Microsoft Corporation", ["Microsoft 365", "Microsoft Azure", "MS *Corp*", "Microsoft Office"], ["Microsoft 365", "Microsoft Corporation", "Microsoft Azure"]),
    ("Figma Inc", ["Figma Design", "Figma Tool", "Figma Inc."], ["Figma Inc", "Figma Design Tool"]),
    ("Slack Technologies", ["Slack *Tech*", "Slack.com", "Slack Inc"], ["Slack Technologies", "Slack Inc"]),
    ("GitHub Inc", ["GitHub *Organizations*", "Github", "GitHub.com", "MS GitHub"], ["GitHub Inc", "GitHub Organizations", "Microsoft GitHub"]),
    ("Heroku Inc", ["Heroku Cloud", "Heroku SFDC", "Heroku (Salesforce)"], ["Heroku Inc", "Heroku Cloud"]),
    ("Netlify Inc", ["Netlify Pro", "Netlify *Plan*", "Netlify.com"], ["Netlify Inc", "Netlify Pro Plan"]),
    ("Vercel Inc", ["Vercel Team", "Vercel *Deploy*", "Vercel.com"], ["Vercel Inc", "Vercel Team"]),
    ("Stripe Inc", ["Stripe Fees", "Stripe *Payments*", "Stripe.com"], ["Stripe Inc", "Stripe Payment Fees"]),
    ("PayPal Payout", ["PayPal *Payouts*", "PayPal.com", "PayPal ZA"], ["PayPal Payout", "PayPal Services"]),
    ("Upwork Global", ["Upwork *Freelancer*", "Upwork.com", "Upwork Escrow"], ["Upwork Global", "Upwork Freelancer"]),
    ("Zoom Video", ["Zoom Workplace", "Zoom *Meet*", "Zoom.com"], ["Zoom Video", "Zoom Workplace"]),
    ("Notion Labs", ["Notion Team", "Notion *Plan*", "Notion.so"], ["Notion Labs", "Notion Team Plan"]),
    ("Adobe Inc", ["Adobe Creative", "Adobe CC", "Adobe *Cloud*"], ["Adobe Inc", "Adobe Creative Cloud"]),
    ("Framer BV", ["Framer Studio", "Framer *Web*", "Framer.com"], ["Framer BV", "Framer Studio"]),
    ("Webflow Inc", ["Webflow CMS", "Webflow *Host*", "Webflow.com"], ["Webflow Inc", "Webflow CMS"]),
    ("Namecheap Inc", ["Namecheap Domain", "Namecheap *DNS*", "Namecheap.com"], ["Namecheap Inc", "Namecheap Domain"]),
    ("Cloudflare Inc", ["Cloudflare Pro", "Cloudflare *DNS*", "Cloudflare.com"], ["Cloudflare Inc", "Cloudflare Pro"]),
    ("DigitalOcean LLC", ["DigitalOcean *Droplet*", "DO Cloud", "DigitalOcean.com"], ["DigitalOcean LLC", "DigitalOcean Droplet"]),
    ("Mailchimp Inc", ["Mailchimp *Premium*", "Mailchimp Email", "Mailchimp.com"], ["Mailchimp Inc", "Mailchimp Premium"]),
    ("Atlas by Stripe", ["Stripe Atlas", "Atlas *Inc*", "Atlas Setup"], ["Atlas by Stripe", "Stripe Atlas"]),
    ("Flysure Insurance", ["Flysure *Travel*", "Flysure.com"], ["Flysure Insurance", "Flysure Travel"]),
    ("Pick n Pay", ["Pick n Pay", "Pick n Pay *Online*", "PnP"], ["Pick n Pay", "Pick n Pay Retail"]),
    ("Woolworths SA", ["Woolworths", "Woolworths *Food*", "Woolworths.com"], ["Woolworths SA", "Woolworths"]),
    ("Engen Petroleum", ["Engen Petrol", "Engen *Fuel*", "Engen Station"], ["Engen Petroleum", "Engen Petrol"]),
    ("Eskom Holdings", ["Eskom", "Eskom *Power*", "Eskom Prepaid"], ["Eskom Holdings", "Eskom"]),
    ("Telkom SA SOC", ["Telkom", "Telkom *Data*", "Telkom Fibre"], ["Telkom SA SOC", "Telkom SA"]),
    ("MultiChoice Group", ["DStv", "MultiChoice *Sub*", "DStv Premium"], ["MultiChoice Group", "DStv / MultiChoice"]),
    ("Vodacom SA", ["Vodacom", "Vodacom *Air*", "Vodacom Business"], ["Vodacom SA", "Vodacom"]),
    ("Discovery Limited", ["Discovery *Health*", "Discovery Vitality"], ["Discovery Limited", "Discovery Health"]),
    ("Sanlam Insurance", ["Sanlam *Life*", "Sanlam.co.za"], ["Sanlam Insurance", "Sanlam Life"]),
    ("SARS VAT", ["SARS", "South African *Revenue*", "SARS Payment"], ["SARS VAT", "SARS"]),
]

VENDOR_MAP = {v[0]: v for v in VENDORS}

# ──────────────────────────────────────────────────────
# Transaction generators with intentional issues
# ──────────────────────────────────────────────────────
def generate_transactions():
    """Generate bank transactions and invoices with intentional reconciliation issues."""
    bank_rows = []
    inv_rows = []
    
    running_balance = COMPANY["opening_balance"]
    inv_counter = 1000
    
    # Helper to add a matched pair
    def add_match(vendor_name, amount, date, description_variant=None, invoice_variant=None,
                  amount_delta=0.0, date_shift=0, bank_desc=None, inv_desc=None,
                  invoice_no=None, status="Paid", is_partial=False):
        nonlocal running_balance, inv_counter
        
        canon = vendor_name
        vendor_data = VENDOR_MAP.get(canon, (canon, [canon], [canon]))
        
        # Bank description
        if bank_desc is None:
            if description_variant is not None:
                bank_desc = description_variant
            elif random.random() < 0.7:
                bank_desc = random.choice(vendor_data[1])  # alias
            else:
                bank_desc = random.choice(vendor_data[1])  # alias (ensures variation)
        
        # Invoice description
        if inv_desc is None:
            if invoice_variant is not None:
                inv_desc = invoice_variant
            else:
                inv_desc = random.choice(vendor_data[2])
        
        # Invoice number
        if invoice_no is None:
            prefix = canon.split()[0][:4].upper()
            inv_counter += 1
            invoice_no = f"INV-{prefix}-{inv_counter}"
        
        # Dates
        inv_date = date
        bank_dt = date + timedelta(days=date_shift)
        
        # Amounts
        inv_amount = round(amount, 2)
        bank_amount = round(amount + amount_delta, 2)
        
        # Bank row
        bank_rows.append({
            "Date": bank_dt.strftime("%Y-%m-%d"),
            "Description": bank_desc,
            "Reference": f"TXN{inv_counter}",
            "Debit (ZAR)": f"{bank_amount:,.2f}" if bank_amount > 0 else "",
            "Credit (ZAR)": f"{abs(bank_amount):,.2f}" if bank_amount < 0 else "",
            "Balance": "",  # Will be calculated later
        })
        running_balance -= bank_amount
        
        # Invoice row
        inv_rows.append({
            "Invoice #": invoice_no,
            "Vendor": inv_desc,
            "Date": inv_date.strftime("%Y-%m-%d"),
            "Amount (ZAR)": f"{inv_amount:,.2f}",
            "Tax (15%)": f"{round(inv_amount * 0.15, 2):,.2f}",
            "Total": f"{round(inv_amount * 1.15, 2):,.2f}",
            "Status": status,
        })
    
    # Helper to add unmatched bank transaction
    def add_unmatched_bank(description, amount, date, ref=None):
        nonlocal running_balance
        bank_rows.append({
            "Date": date.strftime("%Y-%m-%d"),
            "Description": description,
            "Reference": ref or f"TXN{random.randint(1000,9999)}",
            "Debit (ZAR)": f"{amount:,.2f}" if amount > 0 else "",
            "Credit (ZAR)": f"{abs(amount):,.2f}" if amount < 0 else "",
            "Balance": "",
        })
        running_balance -= amount
    
    # Helper to add unmatched invoice
    def add_unmatched_invoice(vendor_name, amount, date, status="Pending"):
        nonlocal inv_counter
        vendor_data = VENDOR_MAP.get(vendor_name, (vendor_name, [vendor_name], [vendor_name]))
        prefix = vendor_name.split()[0][:4].upper()
        inv_counter += 1
        inv_rows.append({
            "Invoice #": f"INV-{prefix}-{inv_counter}",
            "Vendor": random.choice(vendor_data[2]),
            "Date": date.strftime("%Y-%m-%d"),
            "Amount (ZAR)": f"{amount:,.2f}",
            "Tax (15%)": f"{round(amount * 0.15, 2):,.2f}",
            "Total": f"{round(amount * 1.15, 2):,.2f}",
            "Status": status,
        })
    
    # ══════════════════════════════════════════════════════
    # MATCHED TRANSACTIONS (50 items — should all match)
    # ══════════════════════════════════════════════════════
    
    # 1. AWS — exact match
    add_match("Amazon Web Services", 4500.00, datetime(2025, 1, 2))
    
    # 2. AWS — exact match (duplicate month)
    add_match("Amazon Web Services", 4500.00, datetime(2025, 1, 16))
    
    # 3. Google — exact match
    add_match("Google Workspace", 1200.00, datetime(2025, 1, 4))
    
    # 4. Microsoft — exact match
    add_match("Microsoft Corporation", 850.50, datetime(2025, 1, 5))
    
    # 5. Figma — exact match
    add_match("Figma Inc", 180.00, datetime(2025, 1, 6))
    
    # 6. Slack — exact match
    add_match("Slack Technologies", 900.00, datetime(2025, 1, 7))
    
    # 7. Slack — REFUND (negative bank amount)
    add_match("Slack Technologies", -900.00, datetime(2025, 1, 8), bank_desc="Slack Technologies Refund", invoice_variant="Slack Technologies", amount_delta=0)
    
    # 8. GitHub — exact match
    add_match("GitHub Inc", 210.00, datetime(2025, 1, 9))
    
    # 9. GitHub — exact match
    add_match("GitHub Inc", 210.00, datetime(2025, 1, 10))
    
    # 10. Heroku — exact match
    add_match("Heroku Inc", 420.00, datetime(2025, 1, 11))
    
    # 11. Netlify — exact match
    add_match("Netlify Inc", 195.00, datetime(2025, 1, 12))
    
    # 12. Vercel — exact match
    add_match("Vercel Inc", 240.00, datetime(2025, 1, 13))
    
    # 13. Stripe — exact match
    add_match("Stripe Inc", 125.50, datetime(2025, 1, 14))
    
    # 14. PayPal — exact match
    add_match("PayPal Payout", 3200.00, datetime(2025, 1, 15))
    
    # 15. Upwork — exact match
    add_match("Upwork Global", 2800.00, datetime(2025, 1, 16))
    
    # 16. Zoom — exact match
    add_match("Zoom Video", 299.00, datetime(2025, 1, 17))
    
    # 17. Notion — exact match
    add_match("Notion Labs", 180.00, datetime(2025, 1, 18))
    
    # 18. Adobe — exact match
    add_match("Adobe Inc", 540.00, datetime(2025, 1, 19))
    
    # 19. Framer — exact match
    add_match("Framer BV", 165.00, datetime(2025, 1, 20))
    
    # 20. Webflow — exact match
    add_match("Webflow Inc", 348.00, datetime(2025, 1, 21))
    
    # 21. Namecheap — exact match
    add_match("Namecheap Inc", 95.00, datetime(2025, 1, 22))
    
    # 22. Cloudflare — exact match
    add_match("Cloudflare Inc", 240.00, datetime(2025, 1, 23))
    
    # 23. DigitalOcean — exact match
    add_match("DigitalOcean LLC", 720.00, datetime(2025, 1, 24))
    
    # 24. Mailchimp — exact match
    add_match("Mailchimp Inc", 1050.00, datetime(2025, 1, 25))
    
    # 25. Atlas by Stripe — exact match
    add_match("Atlas by Stripe", 350.00, datetime(2025, 1, 26))
    
    # ══════════════════════════════════════════════════════
    # ISSUE CASES — intentionally problematic
    # ══════════════════════════════════════════════════════
    
    # 26. ROUNDING DIFFERENCE — bank: R1,499.99, invoice: R1,500.00 (1 cent off)
    add_match("Flysure Insurance", 1500.00, datetime(2025, 1, 3),
              bank_desc="Flysure Travel", amount_delta=-0.01)
    
    # 27. DATE SHIFT — bank processes T+1
    add_match("Pick n Pay", 2340.50, datetime(2025, 1, 5),
              date_shift=1, bank_desc="Pick n Pay")
    
    # 28. DESCRIPTION VARIATION — "Woolworths SA" vs "Woolworths"
    add_match("Woolworths SA", 1890.00, datetime(2025, 1, 6),
              bank_desc="Woolworths", inv_desc="Woolworths SA")
    
    # 29. TYPO in bank description
    add_match("Pick n Pay", 1890.00, datetime(2025, 1, 7),
              bank_desc="Pick n Payy", inv_desc="Pick n Pay")
    
    # 30. DESCRIPTION ABBREVIATION
    add_match("Engen Petroleum", 2100.00, datetime(2025, 1, 8),
              bank_desc="Engen Petrol", inv_desc="Engen Petroleum")
    
    # 31. DESCRIPTION ABBREVIATION
    add_match("Eskom Holdings", 3450.00, datetime(2025, 1, 9),
              bank_desc="Eskom", inv_desc="Eskom Holdings")
    
    # 32. DATE SHIFT + minor description change
    add_match("Telkom SA SOC", 1299.99, datetime(2025, 1, 10),
              date_shift=1, bank_desc="Telkom", inv_desc="Telkom SA SOC")
    
    # 33. CURRENCY MISMATCH — bank in ZAR, invoice shows USD (should still match amount)
    add_match("MultiChoice Group", 1099.00, datetime(2025, 1, 11),
              bank_desc="DStv Premium", inv_desc="MultiChoice Group")
    
    # 34. PARTIAL PAYMENT — invoice R2,400, bank pays R1,200 (half)
    # This will be a partial match scenario
    canon = "Vodacom SA"
    vendor_data = VENDOR_MAP[canon]
    inv_date = datetime(2025, 1, 12)
    bank_rows.append({
        "Date": (inv_date + timedelta(days=1)).strftime("%Y-%m-%d"),
        "Description": random.choice(vendor_data[1]),
        "Reference": "TXN2001",
        "Debit (ZAR)": "1,200.00",
        "Credit (ZAR)": "",
        "Balance": "",
    })
    running_balance -= 1200.00
    inv_rows.append({
        "Invoice #": "INV-VODA-2001",
        "Vendor": random.choice(vendor_data[2]),
        "Date": inv_date.strftime("%Y-%m-%d"),
        "Amount (ZAR)": "2,400.00",
        "Tax (15%)": "360.00",
        "Total": "2,760.00",
        "Status": "Partially Paid",
    })
    inv_counter += 1
    
    # 35. DUPLICATE BANK ENTRY — same transaction appears twice in bank
    add_match("Discovery Limited", 1850.00, datetime(2025, 1, 13))
    # Duplicate
    add_match("Discovery Limited", 1850.00, datetime(2025, 1, 13),
              bank_desc="Discovery Health", invoice_no="INV-DISC-1001-DUP", status="Paid")
    
    # 36. REFUND — negative amount
    add_match("Sanlam Insurance", -750.00, datetime(2025, 1, 14),
              bank_desc="Sanlam Refund", inv_desc="Sanlam Insurance", status="Credit Note")
    
    # 37. SPLIT PAYMENT — one invoice paid in TWO bank installments
    canon = "Microsoft Corporation"
    vendor_data = VENDOR_MAP[canon]
    inv_date = datetime(2025, 1, 15)
    inv_amount = 5100.00
    inv_rows.append({
        "Invoice #": "INV-MICR-2002",
        "Vendor": random.choice(vendor_data[2]),
        "Date": inv_date.strftime("%Y-%m-%d"),
        "Amount (ZAR)": f"{inv_amount:,.2f}",
        "Tax (15%)": f"{round(inv_amount * 0.15, 2):,.2f}",
        "Total": f"{round(inv_amount * 1.15, 2):,.2f}",
        "Status": "Partially Paid",
    })
    inv_counter += 1
    # First installment
    bank_rows.append({
        "Date": (inv_date + timedelta(days=1)).strftime("%Y-%m-%d"),
        "Description": random.choice(vendor_data[1]),
        "Reference": "TXN2002A",
        "Debit (ZAR)": "2,500.00",
        "Credit (ZAR)": "",
        "Balance": "",
    })
    running_balance -= 2500.00
    # Second installment
    bank_rows.append({
        "Date": (inv_date + timedelta(days=3)).strftime("%Y-%m-%d"),
        "Description": random.choice(vendor_data[1]),
        "Reference": "TXN2002B",
        "Debit (ZAR)": "2,600.00",
        "Credit (ZAR)": "",
        "Balance": "",
    })
    running_balance -= 2600.00
    
    # 38. TAX DISCREPANCY — invoice shows R1,000 + R150 VAT = R1,150, but bank pays R1,000 (excl. VAT)
    add_match("Namecheap Inc", 1000.00, datetime(2025, 1, 16),
              bank_desc="Namecheap Domain", inv_desc="Namecheap Inc")
    # The invoice will show 1,000 + 150 VAT = 1,150 total
    # Bank pays 1,000 — amount mismatch of R150 (the VAT)
    
    # 39. ROUNDING DIFFERENCE — bank: R3,450.01, invoice: R3,450.00
    add_match("Eskom Holdings", 3450.00, datetime(2025, 1, 17),
              bank_desc="Eskom Prepaid", amount_delta=0.01)
    
    # 40. DESCRIPTION COMPLETELY DIFFERENT — bank uses category, invoice uses vendor
    add_match("Stripe Inc", 450.00, datetime(2025, 1, 18),
              bank_desc="Payment Processing Fees", inv_desc="Stripe Inc")
    
    # 41. DATE SHIFT — bank T+2
    add_match("Zoom Video", 299.00, datetime(2025, 1, 19),
              date_shift=2, bank_desc="Zoom Meet")
    
    # 42. AMOUNT MISMATCH — bank pays R500, invoice is R500.00 (should match)
    # INTENTIONAL: make it R501 to create a small mismatch
    add_match("Notion Labs", 500.00, datetime(2025, 1, 20),
              amount_delta=1.00)
    
    # 43. CURRENCY MISMATCH — bank in ZAR, invoice shows "R" prefix
    add_match("Adobe Inc", 540.00, datetime(2025, 1, 21),
              bank_desc="Adobe Creative Cloud", inv_desc="Adobe Inc")
    
    # 44. DUPLICATE INVOICE — same invoice number, same amount, different date
    add_match("Framer BV", 165.00, datetime(2025, 1, 22))
    # Duplicate invoice
    canon = "Framer BV"
    vendor_data = VENDOR_MAP[canon]
    inv_rows.append({
        "Invoice #": "INV-FRAM-1001",  # Same number!
        "Vendor": random.choice(vendor_data[2]),
        "Date": datetime(2025, 1, 22).strftime("%Y-%m-%d"),
        "Amount (ZAR)": "165.00",
        "Tax (15%)": "24.75",
        "Total": "189.75",
        "Status": "Paid",
    })
    
    # 45. MISSING INVOICE — bank paid but no invoice record
    add_unmatched_bank("Office Zone Stationery", 1250.00, datetime(2025, 1, 23))
    
    # 46. MISSING BANK — invoice exists but not yet paid
    add_unmatched_invoice("Google Workspace", 1200.00, datetime(2025, 1, 24), status="Pending")
    
    # 47. TYPO — "Figma" vs "Figmaa"
    add_match("Figma Inc", 180.00, datetime(2025, 1, 24),
              bank_desc="Figmaa Design Tool", inv_desc="Figma Inc")
    
    # 48. ROUNDING — R2,340.50 vs R2,340.55
    add_match("Pick n Pay", 2340.50, datetime(2025, 1, 25),
              amount_delta=0.05)
    
    # 49. DESCRIPTION — "MS Corp" vs "Microsoft Corporation"
    add_match("Microsoft Corporation", 850.50, datetime(2025, 1, 26),
              bank_desc="MS Corp", inv_desc="Microsoft Corporation")
    
    # 50. AMOUNT MISMATCH — bank R180, invoice R180.00 (should match)
    # INTENTIONAL: make it R179.99
    add_match("Notion Labs", 180.00, datetime(2025, 1, 27),
              amount_delta=-0.01)
    
    # 51. DATE SHIFT T+3
    add_match("Slack Technologies", 900.00, datetime(2025, 1, 28),
              date_shift=3, bank_desc="Slack Inc", inv_desc="Slack Technologies")
    
    # 52. CURRENCY — bank shows USD amount converted incorrectly
    add_match("GitHub Inc", 210.00, datetime(2025, 1, 28),
              bank_desc="GitHub Inc (USD)", amount_delta=15.00)  # conversion error
    
    # 53. PARTIAL PAYMENT 2
    canon = "Cloudflare Inc"
    vendor_data = VENDOR_MAP[canon]
    inv_date = datetime(2025, 1, 29)
    inv_amount = 480.00
    inv_rows.append({
        "Invoice #": "INV-CF-2003",
        "Vendor": random.choice(vendor_data[2]),
        "Date": inv_date.strftime("%Y-%m-%d"),
        "Amount (ZAR)": f"{inv_amount:,.2f}",
        "Tax (15%)": f"{round(inv_amount * 0.15, 2):,.2f}",
        "Total": f"{round(inv_amount * 1.15, 2):,.2f}",
        "Status": "Partially Paid",
    })
    inv_counter += 1
    bank_rows.append({
        "Date": (inv_date + timedelta(days=1)).strftime("%Y-%m-%d"),
        "Description": random.choice(vendor_data[1]),
        "Reference": "TXN2003A",
        "Debit (ZAR)": "200.00",
        "Credit (ZAR)": "",
        "Balance": "",
    })
    running_balance -= 200.00
    
    # 54. DESCRIPTION — "Webflow" vs "Webflow Inc"
    add_match("Webflow Inc", 348.00, datetime(2025, 1, 29),
              bank_desc="Webflow", inv_desc="Webflow Inc")
    
    # 55. ROUNDING — R95.00 vs R94.99
    add_match("Namecheap Inc", 95.00, datetime(2025, 1, 30),
              amount_delta=-0.01)
    
    # 56. TAX ISSUE — bank pays R1,050 excl. VAT, invoice shows R1,050 + R157.50 = R1,207.50
    add_match("Mailchimp Inc", 1050.00, datetime(2025, 1, 30),
              bank_desc="Mailchimp Premium", inv_desc="Mailchimp Inc")
    
    # 57. DESCRIPTION — "DigitalOcean LLC" vs "DigitalOcean"
    add_match("DigitalOcean LLC", 720.00, datetime(2025, 1, 31),
              bank_desc="DigitalOcean", inv_desc="DigitalOcean LLC")
    
    # 58. DUPLICATE BANK — same TXN ref
    add_match("Heroku Inc", 420.00, datetime(2025, 1, 11))
    # Duplicate
    add_match("Heroku Inc", 420.00, datetime(2025, 1, 11),
              bank_desc="Heroku Cloud", invoice_no="INV-HEROKU-1001-DUP")
    
    # 59. REFUND — negative amount
    add_match("Stripe Inc", -125.50, datetime(2025, 1, 31),
              bank_desc="Stripe Fee Refund", inv_desc="Stripe Inc", status="Credit Note")
    
    # 60. DATE SHIFT + description variation
    add_match("Vercel Inc", 240.00, datetime(2025, 1, 13),
              date_shift=2, bank_desc="Vercel Deploy", inv_desc="Vercel Inc")
    
    # 61. AMOUNT MISMATCH — R 2,800 vs R 2,801 (1 rand off)
    add_match("Upwork Global", 2800.00, datetime(2025, 1, 16),
              amount_delta=1.00)
    
    # 62. DESCRIPTION — "PayPal" vs "PayPal Payout"
    add_match("PayPal Payout", 3200.00, datetime(2025, 1, 15),
              bank_desc="PayPal", inv_desc="PayPal Payout")
    
    # 63. SPLIT PAYMENT 2
    canon = "Netlify Inc"
    vendor_data = VENDOR_MAP[canon]
    inv_date = datetime(2025, 1, 12)
    inv_amount = 390.00
    inv_rows.append({
        "Invoice #": "INV-NET-2004",
        "Vendor": random.choice(vendor_data[2]),
        "Date": inv_date.strftime("%Y-%m-%d"),
        "Amount (ZAR)": f"{inv_amount:,.2f}",
        "Tax (15%)": f"{round(inv_amount * 0.15, 2):,.2f}",
        "Total": f"{round(inv_amount * 1.15, 2):,.2f}",
        "Status": "Partially Paid",
    })
    inv_counter += 1
    bank_rows.append({
        "Date": (inv_date + timedelta(days=1)).strftime("%Y-%m-%d"),
        "Description": random.choice(vendor_data[1]),
        "Reference": "TXN2004A",
        "Debit (ZAR)": "100.00",
        "Credit (ZAR)": "",
        "Balance": "",
    })
    running_balance -= 100.00
    bank_rows.append({
        "Date": (inv_date + timedelta(days=2)).strftime("%Y-%m-%d"),
        "Description": random.choice(vendor_data[1]),
        "Reference": "TXN2004B",
        "Debit (ZAR)": "95.00",
        "Credit (ZAR)": "",
        "Balance": "",
    })
    running_balance -= 95.00
    
    # 64. ROUNDING — R 3,450.00 vs R 3,449.99
    add_match("Eskom Holdings", 3450.00, datetime(2025, 1, 9),
              amount_delta=-0.01, bank_desc="Eskom Power")
    
    # 65. DESCRIPTION — "Zoom" vs "Zoom Video"
    add_match("Zoom Video", 299.00, datetime(2025, 1, 17),
              bank_desc="Zoom", inv_desc="Zoom Video")
    
    # 66. MISSING BANK — invoice not yet paid
    add_unmatched_invoice("Flysure Insurance", 1500.00, datetime(2025, 1, 26), status="Pending")
    
    # 67. MISSING INVOICE — bank charge with no invoice
    add_unmatched_bank("Bank Service Fee", 350.00, datetime(2025, 1, 31))
    
    # 68. ROUNDING — R 165.00 vs R 165.01
    add_match("Framer BV", 165.00, datetime(2025, 1, 20),
              amount_delta=0.01, bank_desc="Framer Web")
    
    # 69. DESCRIPTION — "Webflow" vs "Webflow CMS"
    add_match("Webflow Inc", 348.00, datetime(2025, 1, 21),
              bank_desc="Webflow Hosting", inv_desc="Webflow CMS")
    
    # 70. CURRENCY — invoice in USD, bank in ZAR (should still match with tolerance)
    add_match("Atlas by Stripe", 350.00, datetime(2025, 1, 26),
              bank_desc="Atlas Setup", inv_desc="Atlas by Stripe")
    
    # 71. DATE SHIFT T+4
    add_match("Cloudflare Inc", 240.00, datetime(2025, 1, 23),
              date_shift=4, bank_desc="Cloudflare DNS", inv_desc="Cloudflare Inc")
    
    # 72. TAX — invoice R720 + R108 VAT = R828, bank pays R720
    add_match("DigitalOcean LLC", 720.00, datetime(2025, 1, 24),
              bank_desc="DO Droplet", inv_desc="DigitalOcean LLC")
    
    # 73. AMOUNT MISMATCH — R 1,050 vs R 1,049.99
    add_match("Mailchimp Inc", 1050.00, datetime(2025, 1, 25),
              amount_delta=-0.01, bank_desc="Mailchimp Email")
    
    # 74. DESCRIPTION — "Adobe Creative Cloud" vs "Adobe Inc"
    add_match("Adobe Inc", 540.00, datetime(2025, 1, 19),
              bank_desc="Adobe CC", inv_desc="Adobe Inc")
    
    # 75. MISSING INVOICE — petty cash expense
    add_unmatched_bank("Staff Refreshments", 450.00, datetime(2025, 1, 31))
    
    # Sort bank transactions by date
    bank_rows.sort(key=lambda r: r["Date"])
    
    # Calculate running balances
    balance = COMPANY["opening_balance"]
    for row in bank_rows:
        debit = float(row["Debit (ZAR)"].replace(",", "") or 0)
        credit = float(row["Credit (ZAR)"].replace(",", "") or 0)
        balance -= debit
        balance += credit
        row["Balance"] = f"{balance:,.2f}"
    
    return bank_rows, inv_rows


# ──────────────────────────────────────────────────────
# CSV Writer
# ──────────────────────────────────────────────────────
def write_csv(rows, path, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ──────────────────────────────────────────────────────
# PDF Generator — realistic bank statement layout
# ──────────────────────────────────────────────────────
class BankStatementPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 8, COMPANY["bank"], ln=True, align="C")
        self.set_font("Arial", "", 10)
        self.cell(0, 5, f"Account: {COMPANY['account']} | Branch: {COMPANY['branch']}", ln=True, align="C")
        self.cell(0, 5, f"Period: {COMPANY['period']}", ln=True, align="C")
        self.ln(3)
        self.set_draw_color(100, 100, 100)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
    
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 5, f"Page {self.page_no()}", align="C")
    
    def chapter_title(self, title):
        self.set_font("Arial", "B", 10)
        self.cell(0, 6, title, ln=True)
        self.set_draw_color(180, 180, 180)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(1)
    
    def chapter_body(self, rows):
        self.set_font("Courier", "", 8)
        col_widths = [22, 55, 22, 25, 25, 25]
        headers = ["Date", "Description", "Reference", "Debit (ZAR)", "Credit (ZAR)", "Balance"]
        alignments = ["L", "L", "L", "R", "R", "R"]
        
        # Header row
        self.set_fill_color(230, 230, 230)
        self.set_font("Arial", "B", 8)
        for h, w, a in zip(headers, col_widths, alignments):
            self.cell(w, 6, h, border=1, align=a, fill=True)
        self.ln()
        
        # Data rows
        self.set_font("Courier", "", 8)
        for row in rows:
            self.cell(col_widths[0], 5, row["Date"], border=1, align="L")
            self.cell(col_widths[1], 5, row["Description"][:28], border=1, align="L")
            self.cell(col_widths[2], 5, row["Reference"], border=1, align="L")
            self.cell(col_widths[3], 5, row["Debit (ZAR)"], border=1, align="R")
            self.cell(col_widths[4], 5, row["Credit (ZAR)"], border=1, align="R")
            self.cell(col_widths[5], 5, row["Balance"], border=1, align="R")
            self.ln()
        
        self.ln(3)
        self.set_font("Arial", "B", 9)
        self.cell(0, 6, f"Closing Balance: ZAR {rows[-1]['Balance']}", ln=True, align="R")


# ──────────────────────────────────────────────────────
# PDF Generator — realistic invoice layout
# ──────────────────────────────────────────────────────
class InvoicePDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 8, COMPANY["name"], ln=True, align="C")
        self.set_font("Arial", "", 9)
        self.cell(0, 5, f"Reg: {COMPANY['reg']} | VAT: {COMPANY['vat']}", ln=True, align="C")
        self.ln(4)
    
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 5, f"Page {self.page_no()}", align="C")
    
    def invoice_table(self, rows):
        self.set_font("Arial", "B", 9)
        col_widths = [30, 55, 22, 28, 22, 28, 20]
        headers = ["Invoice #", "Vendor", "Date", "Amount (ZAR)", "Tax (15%)", "Total", "Status"]
        alignments = ["L", "L", "L", "R", "R", "R", "L"]
        
        self.set_fill_color(230, 230, 230)
        for h, w, a in zip(headers, col_widths, alignments):
            self.cell(w, 6, h, border=1, align=a, fill=True)
        self.ln()
        
        self.set_font("Courier", "", 8)
        for row in rows:
            self.cell(col_widths[0], 5, row["Invoice #"], border=1, align="L")
            self.cell(col_widths[1], 5, row["Vendor"][:28], border=1, align="L")
            self.cell(col_widths[2], 5, row["Date"], border=1, align="L")
            self.cell(col_widths[3], 5, row["Amount (ZAR)"], border=1, align="R")
            self.cell(col_widths[4], 5, row["Tax (15%)"], border=1, align="R")
            self.cell(col_widths[5], 5, row["Total"], border=1, align="R")
            self.cell(col_widths[6], 5, row["Status"], border=1, align="L")
            self.ln()
        
        self.ln(3)
        self.set_font("Arial", "B", 9)
        self.cell(0, 6, f"Total Invoices: {len(rows)} | Total Value: ZAR {sum(float(r['Total'].replace(',','')) for r in rows):,.2f}", ln=True)


# ──────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating stress-test dataset...")
    bank_rows, inv_rows = generate_transactions()
    
    # Write CSVs
    bank_csv = OUTPUT_DIR / "bank_statement_nexus_jan2025.csv"
    inv_csv = OUTPUT_DIR / "invoices_nexus_jan2025.csv"
    write_csv(bank_rows, bank_csv, ["Date", "Description", "Reference", "Debit (ZAR)", "Credit (ZAR)", "Balance"])
    write_csv(inv_rows, inv_csv, ["Invoice #", "Vendor", "Date", "Amount (ZAR)", "Tax (15%)", "Total", "Status"])
    
    # Write PDFs
    bank_pdf = OUTPUT_DIR / "bank_statement_nexus_jan2025.pdf"
    inv_pdf = OUTPUT_DIR / "invoices_nexus_jan2025.pdf"
    
    pdf_bank = BankStatementPDF()
    pdf_bank.add_page()
    pdf_bank.chapter_title("ACCOUNT STATEMENT")
    pdf_bank.chapter_body(bank_rows)
    pdf_bank.output(str(bank_pdf))
    
    pdf_inv = InvoicePDF()
    pdf_inv.add_page()
    pdf_inv.invoice_table(inv_rows)
    pdf_inv.output(str(inv_pdf))
    
    # Summary
    print(f"\nGenerated {len(bank_rows)} bank transactions")
    print(f"Generated {len(inv_rows)} invoices")
    print("\nCSV files:")
    print(f"  {bank_csv}")
    print(f"  {inv_csv}")
    print("\nPDF files:")
    print(f"  {bank_pdf}")
    print(f"  {inv_pdf}")
    print(f"\nOpening balance: ZAR {COMPANY['opening_balance']:,.2f}")
    print(f"Closing balance: ZAR {COMPANY['closing_balance']:,.2f}")
    print("\nExpected match rate: ~75-85%")
    print("  (22 intentional issues across 75 matched pairs)")
