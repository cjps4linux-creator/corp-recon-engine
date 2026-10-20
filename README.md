<h1 align="center">Corp Recon Engine</h1>

<p align="center"><b>Reconcile bank statements against invoices with fuzzy vendor matching, OCR fallback and professional PDF reporting.</b></p>

<p align="center">
  <a href="https://github.com/cjps4linux-creator/corp-recon-engine/actions/workflows/ci.yml"><img src="https://github.com/cjps4linux-creator/corp-recon-engine/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/license-MIT-0a7563" alt="License: MIT">
  <img src="https://img.shields.io/badge/python-3.11%2B-3776ab" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-8a5800" alt="Platforms">
  <img src="https://img.shields.io/badge/no_account-no_telemetry-0a7563" alt="No account, no telemetry">
</p>

---

## What it does

Upload a **bank statement PDF** and an **invoice PDF**. The engine extracts
transactions from both, normalises vendor names, matches them with fuzzy
scoring, and produces a reconciliation report as CSV and a branded PDF.

- **PDF text extraction** — `pdfplumber` / `pypdf`, with `PyMuPDF` and
  `Pillow` fallback for layout-heavy documents
- **OCR fallback** — `pytesseract` for scanned statements that carry no text layer
- **Vendor normalisation** — a curated alias table plus typo correction
  (`payy` → `pay`, `amercian` → `american`, …)
- **Fuzzy matching** — `rapidfuzz` scoring with a configurable threshold
- **Report generation** — `fpdf2` branded PDF with an executive summary,
  KPI dashboard, evidence table, unmatched items, and action items
- **Desktop UI** — Gradio, launched from the desktop with one click

## Requirements

- Python 3.11+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) — only needed for
  scanned statements without a text layer

## Install

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## Run

```bash
python recon_engine.py
```

Or double-click `launch.bat` / `launch-recon.vbs` on Windows.

## Generate test fixtures

The repository ships small CSV/PDF fixtures. The large scanned samples are
generated locally rather than committed:

```bash
python create_all_test_pdfs.py
```

## Module map

| Module | Responsibility |
|--------|----------------|
| `recon_engine.py` | Gradio UI and orchestration |
| `pdf_extractor.py` | Text/OCR extraction from PDFs |
| `vendor_normalizer.py` | Typo correction and alias resolution |
| `vendor_aliases.py` | Curated vendor alias table |
| `report_generator.py` | Branded PDF report generation |

## Licence

MIT — see [LICENSE](LICENSE).

---

## Credits

Built by **Conrad CJ Wilson** — [GitHub](https://github.com/cjps4linux-creator) · [LinkedIn](https://linkedin.com/in/conradcjwilson)

`conradcjwilson0@gmail.com`
