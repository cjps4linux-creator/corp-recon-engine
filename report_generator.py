"""
Enhanced Reconciliation Report Generator
=========================================
Multi-layered professional report with:
- Branded cover with confidential watermark
- Executive summary with KPI dashboard
- Evidence & Analysis layer ( WHY items matched/unmatched )
- Detailed matched transactions with match quality indicators
- Unmatched bank with closest-match evidence
- Unmatched invoices with status tracking
- Action Items & Recommendations
- Sign-off page with digital signature blocks
- Methodology appendix
"""

from fpdf import FPDF
from datetime import datetime
from typing import Dict, List, Any

# ── Color Palette ──────────────────────────────────
NAVY = "#1a2332"
GOLD = "#c9a84c"
GREEN = "#2d7a4f"
RED = "#b34040"
AMBER = "#c97a2d"
SLATE = "#4a5568"
LIGHT_BG = "#f7f8fa"
WHITE = "#ffffff"
DARK_TEXT = "#1a202c"
MED_TEXT = "#4a5568"
LIGHT_TEXT = "#718096"

# ── Helper ────────────────────────────────────────
def _c(hex_color: str) -> tuple:
    """Convert #RRGGBB to (r, g, b) tuple."""
    h = hex_color.lstrip('#')
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


# ============================================================
# REPORT CLASS
# ============================================================
class ReconciliationReport(FPDF):
    def __init__(self, company_name: str = "Nexus Digital Solutions (Pty) Ltd"):
        super().__init__('P', 'mm', 'A4')
        self.set_auto_page_break(auto=True, margin=22)
        self.company_name = company_name
        self.data = {}
        self._draw_watermark = False

    # ── HEADER / FOOTER ──────────────────────────────
    def header(self):
        if self.page_no() == 1:
            return
        # Top bar
        self.set_fill_color(*_c(NAVY))
        self.rect(0, 0, 210, 12, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 8)
        self.set_xy(12, 4)
        self.cell(100, 5, self.company_name, 0, 0, 'L')
        self.set_font("Helvetica", "", 8)
        self.cell(88, 5, f"CONFIDENTIAL  |  Page {self.page_no()}", 0, 1, 'R')
        self.set_draw_color(*_c(GOLD))
        self.set_line_width(0.4)
        self.line(12, 12, 200, 12)
        self.ln(3)

    def footer(self):
        self.set_y(-16)
        self.set_draw_color(*_c(SLATE))
        self.set_line_width(0.2)
        self.line(12, self.get_y(), 200, self.get_y())
        self.ln(1.5)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*_c(MED_TEXT))
        s = self.data.get('summary', {})
        self.cell(0, 4,
            f"Generated: {s.get('generated_at', '')}  |  "
            f"Threshold: {s.get('threshold_used', '')}%  |  "
            f"Tolerance: {s.get('tolerance_used', '')}%  |  "
            f"ReconEngine v2.0",
            0, 1, 'C')

    # ── SECTION HELPERS ──────────────────────────────
    def section_banner(self, title: str, subtitle: str = ""):
        self.ln(2)
        self.set_fill_color(*_c(NAVY))
        self.rect(12, self.get_y(), 186, 10, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 11)
        self.set_xy(16, self.get_y() + 2.5)
        self.cell(160, 5, title, 0, 1, 'L')
        if subtitle:
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*_c(GOLD))
            self.set_xy(16, self.get_y())
            self.cell(160, 4, subtitle, 0, 1, 'L')
        self.set_text_color(*_c(DARK_TEXT))
        self.ln(2)

    def kpi_row(self, kpis: List[Dict]):
        """Render a row of KPI metric cards."""
        card_w = 58
        gap = 6
        x_start = 12
        y = self.get_y()
        for i, kpi in enumerate(kpis):
            x = x_start + i * (card_w + gap)
            # Card background
            bg = kpi.get('bg', NAVY)
            self.set_fill_color(*_c(bg))
            self.rect(x, y, card_w, 24, 'F')
            # Gold top accent
            self.set_fill_color(*_c(GOLD))
            self.rect(x, y, card_w, 2, 'F')
            # Value
            self.set_text_color(255, 255, 255)
            self.set_font("Helvetica", "B", 16)
            self.set_xy(x, y + 5)
            self.cell(card_w, 8, kpi['value'], 0, 1, 'C')
            # Label
            self.set_font("Helvetica", "", 8)
            self.set_text_color(220, 220, 220)
            self.set_xy(x, y + 15)
            self.cell(card_w, 5, kpi['label'], 0, 1, 'C')
        self.set_text_color(*_c(DARK_TEXT))
        self.set_y(y + 28)

    def evidence_box(self, title: str, items: List[str], color: str = NAVY):
        """Render an evidence/analysis box with colored left border."""
        self.ln(1)
        y = self.get_y()
        # Left accent bar
        self.set_fill_color(*_c(color))
        self.rect(12, y, 3, 6 + len(items) * 5.5, 'F')
        # Title
        self.set_xy(18, y + 1)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*_c(color))
        self.cell(0, 5, title, 0, 1, 'L')
        # Items
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*_c(MED_TEXT))
        for item in items:
            self.set_xy(18, self.get_y())
            self.cell(3, 4, "-", 0, 0, 'L')
            self.multi_cell(175, 4.5, item)
        self.set_text_color(*_c(DARK_TEXT))
        self.ln(2)

    def draw_table(self, headers: List[str], rows: List[List[str]],
                   col_widths: List[float], header_color: str = NAVY,
                   alt_row: str = LIGHT_BG, status_col: int = -1,
                   amount_cols: List[int] = None):
        if not rows:
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(*_c(MED_TEXT))
            self.cell(0, 8, "  No records.", 0, 1, 'L')
            self.set_text_color(*_c(DARK_TEXT))
            return

        avail = 186
        widths = [w / sum(col_widths) * avail for w in col_widths]

        # Header
        self.set_fill_color(*_c(header_color))
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 7.5)
        for i, h in enumerate(headers):
            self.cell(widths[i], 6.5, f" {h}", 0, 0, 'L', True)
        self.ln()

        # Rows
        self.set_font("Helvetica", "", 7.5)
        for ri, row in enumerate(rows):
            if ri % 2 == 1:
                self.set_fill_color(*_c(alt_row))
                fill = True
            else:
                self.set_fill_color(255, 255, 255)
                fill = True

            if self.get_y() > 265:
                self.add_page()
                self.set_fill_color(*_c(header_color))
                self.set_text_color(255, 255, 255)
                self.set_font("Helvetica", "B", 7.5)
                for i, h in enumerate(headers):
                    self.cell(widths[i], 6.5, f" {h}", 0, 0, 'L', True)
                self.ln()
                self.set_font("Helvetica", "", 7.5)
                self.set_text_color(*_c(DARK_TEXT))

            for ci, cell in enumerate(row):
                align = 'R' if amount_cols and ci in amount_cols else 'L'
                text = str(cell)
                max_c = int(widths[ci] / 1.7)
                if len(text) > max_c:
                    text = text[:max_c - 2] + ".."
                if ci == status_col and status_col >= 0:
                    cl = text.lower()
                    if 'matched' in cl or 'paid' in cl or 'ok' in cl:
                        self.set_text_color(*_c(GREEN))
                    elif 'partial' in cl:
                        self.set_text_color(*_c(AMBER))
                    elif 'unmatched' in cl or 'mismatch' in cl:
                        self.set_text_color(*_c(RED))
                    elif 'credit' in cl or 'refund' in cl:
                        self.set_text_color(*_c("#2563eb"))
                self.cell(widths[ci], 5.5, f" {text}", 0, 0, align, fill)
                self.set_text_color(*_c(DARK_TEXT))
            self.ln()
        self.ln(2)

    def signoff_block(self, preparer: str = "Conrad CJ Wilson", role: str = "Lead Engineer"):
        """Render signature block on a dedicated page."""
        self.add_page()
        self.section_banner("Report Sign-Off", "Authorisation & Certification")
        self.set_y(60)
        # Title
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*_c(NAVY))
        self.cell(0, 10, "This report has been reviewed and certified.", 0, 1, 'C')
        self.ln(8)
        # Signature boxes
        box_w = 80
        box_h = 50
        y = self.get_y()
        for label, name, r in [("Prepared By", preparer, role),
                                 ("Reviewed By", "_________________", "Qualified Accountant"),
                                 ("Approved By", "_________________", "Financial Manager")]:
            x = 12 + (186 - 3 * box_w - 2 * 10) / 2 + (box_w + 10) * ([label, name, r].index(label) if False else 0)
            x = 12 + (186 - 3 * box_w - 20) / 2 + (box_w + 10) * [0, 1, 2][["Prepared By", "Reviewed By", "Approved By"].index(label)]
            self.set_draw_color(*_c(SLATE))
            self.set_line_width(0.3)
            self.rect(x, y, box_w, box_h, 'D')
            # Label
            self.set_xy(x, y + 4)
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(*_c(NAVY))
            self.cell(box_w, 5, label, 0, 1, 'C')
            # Line
            self.set_draw_color(*_c(GOLD))
            self.set_line_width(0.5)
            self.line(x + 10, y + 25, x + box_w - 10, y + 25)
            # Name
            self.set_xy(x, y + 28)
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*_c(DARK_TEXT))
            self.cell(box_w, 6, name, 0, 1, 'C')
            # Role
            self.set_xy(x, y + 35)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*_c(MED_TEXT))
            self.cell(box_w, 5, r, 0, 1, 'C')
            # Date
            self.set_xy(x, y + 42)
            self.set_font("Helvetica", "I", 8)
            self.cell(box_w, 5, "Date: _______________", 0, 1, 'C')

        # Confidentiality notice
        self.set_y(y + box_h + 15)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*_c(RED))
        self.cell(0, 6, "CONFIDENTIAL", 0, 1, 'C')
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*_c(MED_TEXT))
        self.multi_cell(0, 5,
            "This document contains proprietary reconciliation data and is intended solely "
            "for authorised personnel. Unauthorised distribution is prohibited. "
            "All figures should be verified against source documents before financial close.")
        self.ln(3)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*_c(LIGHT_TEXT))
        self.cell(0, 4, f"Generated by ReconEngine v2.0  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  {self.company_name}", 0, 1, 'C')


# ============================================================
# MAIN GENERATOR
# ============================================================
def generate_report(results: Dict, company_name: str = None) -> str:
    pdf = ReconciliationReport(company_name or "Nexus Digital Solutions (Pty) Ltd")
    pdf.data = results
    s = results.get('summary', {})

    # ── PAGE 1: COVER ───────────────────────────────
    pdf.add_page()
    # Full navy background
    pdf.set_fill_color(*_c(NAVY))
    pdf.rect(0, 0, 210, 297, 'F')
    # Gold accent lines
    pdf.set_draw_color(*_c(GOLD))
    pdf.set_line_width(2)
    pdf.line(25, 55, 185, 55)
    pdf.line(25, 200, 185, 200)
    # Company name as watermark
    pdf.set_font("Helvetica", "B", 40)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(25, 100)
    pdf.cell(160, 12, pdf.company_name, 0, 1, 'C')
    # Company logo placeholder
    pdf.set_xy(25, 65)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(160, 14, "RECONCILIATION REPORT", 0, 1, 'C')
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*_c(GOLD))
    pdf.cell(160, 8, "Bank Statement vs. Supplier Invoices", 0, 1, 'C')
    # Divider
    pdf.set_draw_color(*_c(GOLD))
    pdf.set_line_width(1)
    pdf.line(60, 100, 150, 100)
    # Company info
    pdf.set_xy(25, 108)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(200, 200, 200)
    pdf.cell(160, 6, company_name or "Nexus Digital Solutions (Pty) Ltd", 0, 1, 'C')
    pdf.cell(160, 5, f"Report Period: {s.get('period', 'January 2025')}", 0, 1, 'C')
    pdf.cell(160, 5, f"Generated: {s.get('generated_at', datetime.now().strftime('%Y-%m-%d %H:%M'))}", 0, 1, 'C')
    # KPI cards on cover
    pdf.set_y(150)
    kpis = [
        {'label': 'Matched', 'value': str(s.get('matched_count', 0)), 'bg': GREEN},
        {'label': 'Unmatched Bank', 'value': str(s.get('unmatched_bank_count', 0)), 'bg': AMBER},
        {'label': 'Unmatched Invoices', 'value': str(s.get('unmatched_inv_count', 0)), 'bg': RED},
    ]
    pdf.kpi_row(kpis)
    # Match rate highlight
    pdf.set_y(185)
    rate = s.get('match_rate', 0)
    rate_color = GREEN if rate >= 80 else AMBER if rate >= 60 else RED
    pdf.set_fill_color(*_c(rate_color))
    pdf.rect(25, 185, 160, 16, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_xy(25, 188)
    pdf.cell(160, 10, f"Overall Match Rate: {rate}%", 0, 1, 'C')
    # Footer
    pdf.set_y(270)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 6, "CONFIDENTIAL - For Internal Use Only - Not for Distribution", 0, 1, 'C')

    # ── PAGE 2: EXECUTIVE SUMMARY ───────────────────
    pdf.add_page()
    pdf.section_banner("Executive Summary", "Reconciliation Overview & Key Metrics")
    # Narrative
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*_c(MED_TEXT))
    pdf.multi_cell(186, 5.5,
        f"This report presents the reconciliation between {s.get('total_bank', 0)} bank transactions "
        f"and {s.get('total_invoice', 0)} supplier invoices for the period under review. "
        f"Matching was performed using intelligent fuzzy string comparison with amount tolerance validation. "
        f"Each unmatched item includes evidence of the closest match and a specific reason for non-match."
    )
    pdf.ln(4)
    # KPI dashboard
    kpis = [
        {'label': 'Bank Items', 'value': str(s.get('total_bank', 0)), 'bg': NAVY},
        {'label': 'Invoices', 'value': str(s.get('total_invoice', 0)), 'bg': NAVY},
        {'label': f"Match Rate: {rate}%", 'value': str(s.get('matched_count', 0)), 'bg': rate_color},
        {'label': 'Unmatched Bank', 'value': str(s.get('unmatched_bank_count', 0)), 'bg': AMBER},
        {'label': 'Unmatched Invoices', 'value': str(s.get('unmatched_inv_count', 0)), 'bg': RED},
    ]
    pdf.kpi_row(kpis)
    # Threshold info
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*_c(MED_TEXT))
    pdf.cell(0, 5, f"  Threshold: {s.get('threshold_used', '75')}%  |  Amount Tolerance: {s.get('tolerance_used', '5')}%  |  Algorithm: WRatio + Canonical Alias Matching", 0, 1, 'L')
    pdf.ln(3)
    # Evidence summary
    pdf.section_banner("Evidence Summary", "Why items matched or failed to match")
    # Matched evidence
    if results.get('matched_transactions'):
        evidence_items = []
        for m in results['matched_transactions'][:5]:
            evidence_items.append(
                f"'{m.get('bank_desc','')}' matched '{m.get('inv_desc','')}' "
                f"at {m.get('match_score', 0):.0f}% - Amount: {m.get('bank_amount', 0):,.2f} vs {m.get('inv_amount', 0):,.2f}"
            )
        pdf.evidence_box("Top Matched Evidence", evidence_items, GREEN)
    # Unmatched evidence
    if results.get('unmatched_bank'):
        ev = []
        for u in results['unmatched_bank'][:4]:
            ev.append(
                f"'{u.get('bank_desc','')}' ({u.get('bank_amount', 0):,.2f}) - "
                f"Best: '{u.get('best_inv_match','')}' ({u.get('score', 0):.0f}%) - "
                f"Reason: {u.get('reason', 'Unknown')}"
            )
        pdf.evidence_box("Unmatched Bank - Closest Evidence", ev, RED)
    if results.get('unmatched_invoices'):
        ev = []
        for u in results['unmatched_invoices'][:4]:
            ev.append(
                f"'{u.get('inv_desc','')}' ({u.get('inv_amount', 0):,.2f}) - "
                f"Status: {u.get('status', 'Unknown')}"
            )
        pdf.evidence_box("Unmatched Invoices - Status Evidence", ev, AMBER)

    # ── PAGE 3: MATCHED TRANSACTIONS ─────────────────
    pdf.add_page()
    pdf.section_banner("Matched Transactions", "Verified matches with evidence scores")
    if results.get('matched_transactions'):
        headers = ["Date", "Bank Description", "Bank Amt", "Invoice Description", "Inv Amt", "Score", "Category"]
        widths = [20, 38, 20, 38, 20, 12, 28]
        rows = []
        for m in results['matched_transactions']:
            rows.append([
                str(m.get('bank_date', ''))[:10],
                str(m.get('bank_desc', ''))[:28],
                f"{m.get('bank_amount', 0):,.2f}",
                str(m.get('inv_desc', ''))[:28],
                f"{m.get('inv_amount', 0):,.2f}",
                f"{m.get('match_score', 0):.0f}%",
                str(m.get('category', 'Other'))[:18],
            ])
        pdf.draw_table(headers, rows, widths, header_color=GREEN, amount_cols=[2, 4])
    else:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*_c(MED_TEXT))
        pdf.cell(0, 8, "  No matched transactions found.", 0, 1, 'L')
        pdf.set_text_color(*_c(DARK_TEXT))

    # ── PAGE 4: UNMATCHED BANK ──────────────────────
    pdf.add_page()
    pdf.section_banner("Unmatched Bank Transactions", "Bank items without matching invoices - with closest-match evidence")
    if results.get('unmatched_bank'):
        headers = ["Date", "Bank Description", "Bank Amt", "Closest Match", "Match Amt", "Score", "Reason"]
        widths = [20, 38, 20, 38, 20, 12, 28]
        rows = []
        for u in results['unmatched_bank']:
            rows.append([
                str(u.get('bank_date', ''))[:10],
                str(u.get('bank_desc', ''))[:28],
                f"{u.get('bank_amount', 0):,.2f}",
                str(u.get('best_inv_match', '-'))[:28],
                f"{u.get('inv_amount', 0):,.2f}" if u.get('inv_amount') else "-",
                f"{u.get('score', 0):.0f}%" if u.get('score') else "-",
                str(u.get('reason', ''))[:22],
            ])
        pdf.draw_table(headers, rows, widths, header_color=RED, amount_cols=[2, 4], status_col=6)
    else:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*_c(MED_TEXT))
        pdf.cell(0, 8, "  All bank transactions matched.", 0, 1, 'L')
        pdf.set_text_color(*_c(DARK_TEXT))

    # ── PAGE 5: UNMATCHED INVOICES ──────────────────
    pdf.add_page()
    pdf.section_banner("Unmatched Invoices", "Invoices without corresponding bank entries")
    if results.get('unmatched_invoices'):
        headers = ["Date", "Invoice Description", "Amount", "Status", "Notes"]
        widths = [20, 55, 25, 35, 71]
        rows = []
        for u in results['unmatched_invoices']:
            rows.append([
                str(u.get('inv_date', ''))[:10],
                str(u.get('inv_desc', ''))[:40],
                f"{u.get('inv_amount', 0):,.2f}",
                str(u.get('status', 'Unknown'))[:30],
                str(u.get('reason', ''))[:55],
            ])
        pdf.draw_table(headers, rows, widths, header_color=AMBER, amount_cols=[2], status_col=3)
    else:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*_c(MED_TEXT))
        pdf.cell(0, 8, "  All invoices matched to bank entries.", 0, 1, 'L')
        pdf.set_text_color(*_c(DARK_TEXT))

    # ── PAGE 6: ACTION ITEMS & RECOMMENDATIONS ──────
    pdf.add_page()
    pdf.section_banner("Action Items & Recommendations", "Prioritised remediation steps")
    # Derive action items from unmatched data
    actions = []
    unmatched_bank_reasons = {}
    for u in results.get('unmatched_bank', []):
        r = u.get('reason', 'Other')
        unmatched_bank_reasons[r] = unmatched_bank_reasons.get(r, 0) + 1
    for u in results.get('unmatched_invoices', []):
        r = u.get('reason', 'Other')
        unmatched_bank_reasons[r] = unmatched_bank_reasons.get(r, 0) + 1

    reason_map = {
        'Amount Mismatch': ('High', 'Verify invoice amounts against bank debits. Check for partial payments, VAT discrepancies, or currency conversion errors.'),
        'Low Description Match': ('Medium', 'Review vendor name variations. Update vendor alias map in ReconEngine to improve future matching.'),
        'Invoice Already Matched': ('High', 'Duplicate bank entry detected. Verify with bank statement and mark as duplicate or investigate double-charge.'),
        'Unmatched (No Bank Entry)': ('Medium', 'Invoice has no corresponding bank transaction. Verify payment status - may be pending, on credit terms, or not yet processed.'),
        'Partially Paid': ('Low', 'Invoice is partially paid. Track remaining balance and schedule follow-up payment.'),
        'Refund/Credit Note': ('Low', 'Negative amount detected. Verify refund status and apply as credit against future invoices.'),
    }

    priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
    sorted_reasons = sorted(unmatched_bank_reasons.items(), key=lambda x: priority_order.get(reason_map.get(x[0], ('Medium', ''))[0], 1))

    for reason, count in sorted_reasons:
        priority, action = reason_map.get(reason, ('Medium', 'Manual review required.'))
        actions.append({'priority': priority, 'reason': reason, 'count': count, 'action': action})

    for a in actions:
        # Priority badge
        pri_color = RED if a['priority'] == 'High' else AMBER if a['priority'] == 'Medium' else GREEN
        pdf.set_fill_color(*_c(pri_color))
        pdf.rect(12, pdf.get_y(), 3, 14, 'F')
        pdf.set_xy(18, pdf.get_y())
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*_c(NAVY))
        pdf.cell(0, 5, f"[{a['priority']}] {a['reason']}  ({a['count']} items)", 0, 1, 'L')
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*_c(MED_TEXT))
        pdf.set_x(18)
        pdf.multi_cell(170, 4.5, a['action'])
        pdf.ln(2)

    # General recommendations
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*_c(NAVY))
    pdf.cell(0, 6, "General Recommendations:", 0, 1, 'L')
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*_c(MED_TEXT))
    recs = [
        "* Maintain vendor alias mappings to improve fuzzy match scores over time.",
        "* Investigate all 'Amount Mismatch' items - may indicate partial payments, VAT errors, or currency issues.",
        "* Follow up on unmatched invoices to confirm payment status before month-end close.",
        "* Review duplicate entries to prevent double-payment.",
        "* Consider lowering the match threshold to 65% if description variations are common in your industry.",
    ]
    for rec in recs:
        pdf.set_x(18)
        pdf.cell(0, 5, rec, 0, 1, 'L')
    pdf.ln(3)

    # ── PAGE 7: METHODOLOGY ─────────────────────────
    pdf.add_page()
    pdf.section_banner("Methodology & Notes", "How this reconciliation was performed")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*_c(MED_TEXT))
    notes = [
        ("Matching Algorithm",
         "Multi-pass fuzzy string matching using rapidfuzz WRatio scorer. "
         "Pass 1: Canonical name matching via vendor alias map (exact match, 100% score). "
         "Pass 2: Normalized description matching (lowercase, stripped, common suffixes removed). "
         "Pass 3: Raw fuzzy matching as fallback."),
        ("Amount Validation",
         "Matched pairs must have amounts within the configured tolerance percentage. "
         "Absolute values are compared (bank outflows treated as positive for comparison). "
         "Rounding differences of ±1 cent are automatically accepted at 5% tolerance."),
        ("One-to-One Matching",
         "Each invoice can match at most one bank transaction. "
         "Subsequent bank transactions matching the same invoice are flagged as 'Invoice Already Matched'. "
         "This prevents false positives from duplicate entries."),
        ("Description Normalization",
         "Bank and invoice descriptions are normalized before matching: lowercase conversion, "
         "whitespace stripping, common suffixes removed (Inc, LLC, Pty, Ltd, SA, etc.). "
         "Vendor alias maps provide canonical name resolution."),
        ("Categorization",
         "Rule-based keyword matching on bank descriptions. Categories include: Cloud & Software, "
         "Utilities, Telecommunications, Retail & Supplies, Insurance, Professional Services, Other."),
        ("Data Sources",
         "Bank statements and invoices can be provided as CSV, Excel (.xlsx), or PDF. "
         "PDF extraction uses pdfplumber with heuristic column detection and OCR fallback for scanned documents."),
        ("Limitations",
         "This report is generated automatically and does not constitute financial advice. "
         "All matches should be verified by a qualified accountant before financial close. "
         "The engine does not perform FX conversion - amounts are compared in their original currency."),
        ("Threshold Guidance",
         "Higher thresholds (85%+) reduce false positives but may miss legitimate matches with description variations. "
         "Lower thresholds (60-70%) increase recall but require more manual review. "
         "Recommended: 75% for most use cases."),
    ]
    for title, body in notes:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*_c(NAVY))
        pdf.cell(0, 6, f"  {title}", 0, 1, 'L')
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*_c(MED_TEXT))
        pdf.multi_cell(186, 4.5, f"    {body}")
        pdf.ln(2)

    # ── PAGE 8: SIGN-OFF ────────────────────────────
    pdf.signoff_block(preparer="Conrad CJ Wilson", role="Lead Engineer")

    # ── OUTPUT ──────────────────────────────────────
    pdf_path = f"recon_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(pdf_path)
    return pdf_path
