"""Tests for the pure/business-logic helpers in ``recon_engine``.

Every assertion in this file was derived by reading the source and then
*executing* it against the repository's own virtualenv; the expected values
reflect the code's real behaviour, not an idealised version of it.

Scope: pure functions only. No network, no Gradio launch, no model loading.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# clean_string
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, ""),
        (float("nan"), ""),
        (pd.NA, ""),
        (pd.NaT, ""),
        ("", ""),
        ("   ", ""),
        ("  Hello World  ", "hello world"),
        ("ABC", "abc"),
        ("MiXeD CaSe", "mixed case"),
        (123, "123"),
        (12.5, "12.5"),
        (True, "true"),
    ],
)
def test_clean_string(recon_engine, value, expected):
    assert recon_engine.clean_string(value) == expected


def test_clean_string_strips_and_lowercases_only(recon_engine):
    assert recon_engine.clean_string("  \tSpaced Out \n ") == "spaced out"


def test_clean_string_preserves_internal_punctuation(recon_engine):
    assert recon_engine.clean_string("Nando's Head Office") == "nando's head office"


# ---------------------------------------------------------------------------
# parse_amount
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # Missing values become 0.0.
        (None, 0.0),
        (float("nan"), 0.0),
        (pd.NA, 0.0),
        (pd.NaT, 0.0),
        # Native numerics pass straight through.
        (0, 0.0),
        (100, 100.0),
        (100.5, 100.5),
        (-100.5, -100.5),
        (True, 1.0),
        (False, 0.0),
        # Currency symbols are stripped.
        ("R100", 100.0),
        ("R 1 234.56", 1234.56),
        ("$1,000.00", 1000.0),
        ("\u20ac500", 500.0),
        ("\u00a3250.75", 250.75),
        # Parenthesised amounts are accounting negatives.
        ("(1,234.56)", -1234.56),
        ("(100)", -100.0),
        ("R(100.00)", -100.0),
        ("  ($1,000.00)  ", -1000.0),
        # Thousands separators.
        ("1,234.56", 1234.56),
        ("1 234.56", 1234.56),
        ("  42  ", 42.0),
        # Negative and scientific notation.
        ("-50", -50.0),
        ("1e3", 1000.0),
        # Unparsable / empty input degrades to 0.0.
        ("", 0.0),
        ("   ", 0.0),
        ("R", 0.0),
        ("abc", 0.0),
        ("None", 0.0),
        ("0x10", 0.0),
    ],
)
def test_parse_amount(recon_engine, value, expected):
    assert recon_engine.parse_amount(value) == expected


def test_parse_amount_returns_float_type(recon_engine):
    assert isinstance(recon_engine.parse_amount("100"), float)
    assert isinstance(recon_engine.parse_amount(None), float)


def test_parse_amount_keeps_nan_string_as_nan(recon_engine):
    # "nan" is a valid float literal, so it survives parsing as NaN rather
    # than being coerced to 0.0.
    result = recon_engine.parse_amount("nan")
    assert math.isnan(result)


def test_parse_amount_european_decimal_is_misread(recon_engine):
    # Documented quirk: commas are removed and '.' is treated as the decimal
    # separator, so "1.234,56" becomes 1.23456 rather than 1234.56.
    assert recon_engine.parse_amount("1.234,56") == pytest.approx(1.23456)


def test_parse_amount_unsupported_currency_symbols_yield_zero(recon_engine):
    assert recon_engine.parse_amount("\u00a5100") == 0.0
    assert recon_engine.parse_amount("\u20b9500") == 0.0


def test_parse_amount_handles_numpy_scalars(recon_engine):
    np = pytest.importorskip("numpy")
    assert recon_engine.parse_amount(np.int64(42)) == 42.0
    assert recon_engine.parse_amount(np.float64(3.5)) == 3.5
    assert recon_engine.parse_amount(np.float64("nan")) == 0.0


# ---------------------------------------------------------------------------
# categorize
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("description", "expected"),
    [
        ("ACME Consulting", "Professional Services"),
        ("Uber Eats trip", "Transportation"),
        ("Shell Ultra City", "Auto & Fuel"),
        ("Starbucks Coffee", "Meals & Entertainment"),
        ("Amazon Web Services", "Cloud & Software"),
        ("Netflix", "Subscriptions"),
        ("QuickBooks Online", "Accounting Software"),
        ("Microsoft 365", "Cloud & Software"),
        ("MTN South Africa", "Telecommunications"),
        ("Vodacom", "Telecommunications"),
        ("Telkom SA SOC", "Telecommunications"),
        ("Eskom Holdings", "Utilities"),
        ("Woolworths", "Retail & Supplies"),
        ("Pick n Pay Hyper", "Retail & Supplies"),
        ("Shoprite", "Retail & Supplies"),
        ("Sasol", "Energy & Fuel"),
        ("Standard Bank", "Banking & Finance"),
        ("ABSA", "Banking & Finance"),
        ("FNB Fee", "Banking & Finance"),
        ("Nedbank", "Banking & Finance"),
        ("Nando's Head Office", "Meals & Entertainment"),
        # No keyword matches -> "Other".
        ("", "Other"),
        ("Mystery Vendor", "Other"),
        # The map has a typo'd key ("engeng"), so "Engen" is *not* categorised.
        ("Engen 1-Stop", "Other"),
    ],
)
def test_categorize(recon_engine, description, expected):
    assert recon_engine.categorize(description) == expected


def test_categorize_is_case_insensitive(recon_engine):
    assert recon_engine.categorize("acme") == recon_engine.categorize("ACME") == "Professional Services"


def test_categorize_uses_first_matching_keyword_in_map_order(recon_engine):
    # "acme" precedes "uber" in CATEGORY_MAP, so it wins.
    assert recon_engine.categorize("acme uber shell") == "Professional Services"


def test_categorize_matches_on_substrings(recon_engine):
    # "shell" is a substring of "Shellfish Co".
    assert recon_engine.categorize("Shellfish Co") == "Auto & Fuel"


def test_categorize_requires_a_string(recon_engine):
    with pytest.raises(AttributeError):
        recon_engine.categorize(None)
    with pytest.raises(AttributeError):
        recon_engine.categorize(float("nan"))


def test_category_map_contains_expected_keys(recon_engine):
    category_map = recon_engine.CATEGORY_MAP
    assert category_map["acme"] == "Professional Services"
    assert category_map["uber"] == "Transportation"
    assert category_map["shell"] == "Auto & Fuel"
    assert category_map["starbucks"] == "Meals & Entertainment"
    assert category_map["amazon"] == "Cloud & Software"
    assert category_map["netflix"] == "Subscriptions"
    assert category_map["quickbooks"] == "Accounting Software"
    assert category_map["microsoft"] == "Cloud & Software"
    for telecom in ("mtn", "vodacom", "telkom"):
        assert category_map[telecom] == "Telecommunications"
    assert category_map["eskom"] == "Utilities"
    # All category values are [lorem]-empty strings.
    assert all(isinstance(v, str) and v for v in category_map.values())


# ---------------------------------------------------------------------------
# detect_description_column
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "column",
    ["description", "name", "ref", "memo", "payee", "transaction", "details", "narrative", "particulars"],
)
def test_detect_description_column_bank_exact_matches(recon_engine, column):
    df = pd.DataFrame({column: ["Acme"], "amount": [1.0]})
    assert recon_engine.detect_description_column(df, is_bank=True) == column


@pytest.mark.parametrize(
    "column",
    [
        "vendor name",
        "vendor",
        "supplier name",
        "supplier",
        "payee name",
        "payee",
        "description",
        "name",
        "ref",
        "memo",
        "details",
        "particulars",
    ],
)
def test_detect_description_column_invoice_exact_matches(recon_engine, column):
    df = pd.DataFrame({column: ["Acme"], "amount": [1.0]})
    assert recon_engine.detect_description_column(df, is_bank=False) == column


def test_detect_description_column_prefers_description_over_name(recon_engine):
    df = pd.DataFrame({"name": ["x"], "description": ["y"]})
    assert recon_engine.detect_description_column(df, is_bank=True) == "description"


def test_detect_description_column_invoice_prefers_vendor_name(recon_engine):
    df = pd.DataFrame({"Description": ["b"], "Vendor Name": ["a"], "amount": [1.0]})
    assert recon_engine.detect_description_column(df, is_bank=False) == "Vendor Name"


def test_detect_description_column_invoice_candidate_order(recon_engine):
    """Invoice-mode candidates are probed in a fixed order.

    The order is: vendor name, vendor, supplier name, supplier, payee name,
    payee, description, name, ref, memo, details, particulars.
    """
    # "vendor name" beats "payee name".
    df = pd.DataFrame({"Payee Name": ["a"], "Vendor Name": ["b"], "amount": [1.0]})
    assert recon_engine.detect_description_column(df, is_bank=False) == "Vendor Name"

    # "vendor" beats "payee name".
    df = pd.DataFrame({"Payee Name": ["a"], "Vendor": ["b"], "amount": [1.0]})
    assert recon_engine.detect_description_column(df, is_bank=False) == "Vendor"

    # "supplier name" beats "payee name".
    df = pd.DataFrame({"Payee Name": ["a"], "Supplier Name": ["b"], "amount": [1.0]})
    assert recon_engine.detect_description_column(df, is_bank=False) == "Supplier Name"

    # "vendor name" beats "payee".
    df = pd.DataFrame({"Payee": ["a"], "Vendor Name": ["b"], "amount": [1.0]})
    assert recon_engine.detect_description_column(df, is_bank=False) == "Vendor Name"


def test_detect_description_column_is_case_and_whitespace_insensitive(recon_engine):
    df = pd.DataFrame({"  DESCRIPTION  ": ["Acme"], "amount": [1.0]})
    assert recon_engine.detect_description_column(df, is_bank=True) == "  DESCRIPTION  "


def test_detect_description_column_falls_back_to_first_usable_column(recon_engine):
    df = pd.DataFrame({"date": ["2025-01-01"], "amount": [1.0], "example": ["sample"]})
    assert recon_engine.detect_description_column(df, is_bank=True) == "example"


def test_detect_description_column_fallback_skips_known_metadata(recon_engine):
    df = pd.DataFrame({"date": ["2025-01-01"], "amount": [1.0], "example": ["sample"]})
    # "date" and "amount" are on the excluded list, so the fallback picks "example".
    assert recon_engine.detect_description_column(df, is_bank=True) == "example"


def test_detect_description_column_fallback_returns_first_column_when_all_excluded(recon_engine):
    # Every column is on the excluded metadata list, so the fallback returns
    # the very first column of the frame.
    df = pd.DataFrame({"date": ["2025-01-01"], "amount": [1.0]})
    assert recon_engine.detect_description_column(df, is_bank=True) == "date"


def test_detect_description_column_substring_match_raises_attribute_error(recon_engine):
    # Regression guard for a real defect: pass 2 calls `.iloc` on a
    # pandas.Index, which has no `.iloc` attribute, so a column that only
    # matches as a *substring* raises AttributeError instead of returning.
    df = pd.DataFrame({"Transaction Details": ["Acme"], "amount": [1.0]})
    with pytest.raises(AttributeError):
        recon_engine.detect_description_column(df, is_bank=True)


def test_detect_description_column_empty_frame_raises(recon_engine):
    with pytest.raises(AttributeError):
        recon_engine.detect_description_column(pd.DataFrame(), is_bank=True)


# ---------------------------------------------------------------------------
# detect_amount_column
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "column",
    ["amount", "value", "debit", "credit", "total", "paid", "payable"],
)
def test_detect_amount_column_tier1_exact_matches(recon_engine, column):
    df = pd.DataFrame({column: [1.0]})
    assert recon_engine.detect_amount_column(df) == column


def test_detect_amount_column_tier1_precedence_amount_before_value(recon_engine):
    df = pd.DataFrame({"Value": [1.0], "Amount": [2.0]})
    assert recon_engine.detect_amount_column(df) == "Amount"


def test_detect_amount_column_tier1_precedence_debit_before_credit(recon_engine):
    df = pd.DataFrame({"Debit": [1.0], "Credit": [2.0]})
    assert recon_engine.detect_amount_column(df) == "Debit"


def test_detect_amount_column_tier1_precedence_total_before_paid(recon_engine):
    df = pd.DataFrame({"Total": [1.0], "Paid": [2.0]})
    assert recon_engine.detect_amount_column(df) == "Total"


def test_detect_amount_column_tier1_precedence_paid_before_payable(recon_engine):
    df = pd.DataFrame({"Payable": [1.0], "Paid": [2.0]})
    assert recon_engine.detect_amount_column(df) == "Paid"


def test_detect_amount_column_substring_match(recon_engine):
    df = pd.DataFrame({"Amount (USD)": [1.0]})
    assert recon_engine.detect_amount_column(df) == "Amount (USD)"


def test_detect_amount_column_balance_is_last_resort(recon_engine):
    df = pd.DataFrame({"Balance": [1.0]})
    assert recon_engine.detect_amount_column(df) == "Balance"


def test_detect_amount_column_prefers_tier1_over_balance(recon_engine):
    df = pd.DataFrame({"Balance": [1.0], "Value": [2.0]})
    assert recon_engine.detect_amount_column(df) == "Value"


def test_detect_amount_column_matches_balance_as_substring(recon_engine):
    df = pd.DataFrame({"Balance Brought Forward": [1.0]})
    assert recon_engine.detect_amount_column(df) == "Balance Brought Forward"


def test_detect_amount_column_numeric_fallback(recon_engine):
    df = pd.DataFrame({"example": ["a"], "sample": [5.0]})
    assert recon_engine.detect_amount_column(df) == "sample"


def test_detect_amount_column_skips_underscore_prefixed_columns(recon_engine):
    df = pd.DataFrame({"_page": [1, 2], "num": [5.0, 6.0]})
    assert recon_engine.detect_amount_column(df) == "num"


def test_detect_amount_column_skips_non_positive_numeric_columns(recon_engine):
    df = pd.DataFrame({"a": [0.0], "b": [5.0]})
    assert recon_engine.detect_amount_column(df) == "b"


def test_detect_amount_column_skips_out_of_range_numeric_columns(recon_engine):
    df = pd.DataFrame({"a": [2e9], "b": [5.0]})
    assert recon_engine.detect_amount_column(df) == "b"


def test_detect_amount_column_falls_back_to_last_column(recon_engine):
    df = pd.DataFrame({"only": ["x"]})
    assert recon_engine.detect_amount_column(df) == "only"


def test_detect_amount_column_is_case_insensitive(recon_engine):
    df = pd.DataFrame({"AMOUNT": [1.0]})
    assert recon_engine.detect_amount_column(df) == "AMOUNT"


def test_detect_amount_column_empty_frame_raises(recon_engine):
    with pytest.raises(AttributeError):
        recon_engine.detect_amount_column(pd.DataFrame())


# ---------------------------------------------------------------------------
# detect_date_column
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "column",
    ["date", "transaction date", "txn date", "posted date", "invoice date", "due date"],
)
def test_detect_date_column_exact_matches(recon_engine, column):
    df = pd.DataFrame({column: ["2025-01-01"]})
    assert recon_engine.detect_date_column(df) == column


def test_detect_date_column_prefers_date_over_invoice_date(recon_engine):
    df = pd.DataFrame({"Invoice Date": ["2025-01-01"], "Date": ["2025-01-02"]})
    assert recon_engine.detect_date_column(df) == "Date"


def test_detect_date_column_prefers_date_over_txn_date(recon_engine):
    df = pd.DataFrame({"Txn Date": ["2025-01-01"], "Date": ["2025-01-02"]})
    assert recon_engine.detect_date_column(df) == "Date"


def test_detect_date_column_returns_none_when_no_date_column(recon_engine):
    df = pd.DataFrame({"example": [1], "sample": [2]})
    assert recon_engine.detect_date_column(df) is None


def test_detect_date_column_does_not_match_on_substring(recon_engine):
    df = pd.DataFrame({"Settlement Date Value": ["2025-01-01"]})
    assert recon_engine.detect_date_column(df) is None


def test_detect_date_column_empty_frame_raises(recon_engine):
    with pytest.raises(AttributeError):
        recon_engine.detect_date_column(pd.DataFrame())


# ---------------------------------------------------------------------------
# process_reconciliation (end-to-end, file based)
# ---------------------------------------------------------------------------

class _Upload:
    """Minimal stand-in for a Gradio ``gr.File`` object."""

    def __init__(self, path: Path) -> None:
        self.name = str(path)


@pytest.fixture()
def recon_workspace(tmp_path, monkeypatch):
    """Run the engine with the CWD pointed at an isolated tmp directory.

    ``process_reconciliation`` writes its CSV/PDF output relative to the
    current working directory, so the CWD is moved into ``tmp_path`` to keep
    the repository clean.
    """
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _write_csv(directory: Path, name: str, text: str) -> Path:
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path


def test_process_reconciliation_matches_shared_descriptions(recon_engine, recon_workspace):
    bank = _write_csv(
        recon_workspace,
        "bank.csv",
        "date,description,amount\n"
        "2025-01-02,MTN South Africa,-899.00\n"
        "2025-01-03,Vodacom Pty Ltd,-1250.50\n"
        "2025-01-05,Shell Ultra City,-450.00\n",
    )
    invoice = _write_csv(
        recon_workspace,
        "invoice.csv",
        "date,description,amount\n"
        "2025-01-02,MTN South Africa,899.00\n"
        "2025-01-03,Vodacom Pty Ltd,1250.50\n"
        "2025-01-05,Shell Ultra City,450.00\n",
    )

    results = recon_engine.process_reconciliation(_Upload(bank), _Upload(invoice))

    assert len(results["matched_transactions"]) == 3
    assert results["unmatched_bank"] == []
    assert results["unmatched_invoices"] == []
    assert results["summary"]["matched_count"] == 3
    assert results["summary"]["match_rate"] == 100.0
    assert results["summary"]["total_bank"] == 3
    assert results["summary"]["total_invoice"] == 3

    methods = {m["bank_desc"]: m["match_method"] for m in results["matched_transactions"]}
    assert methods["MTN South Africa"] == "Canonical Match"

    categories = {m["bank_desc"]: m["category"] for m in results["matched_transactions"]}
    assert categories["MTN South Africa"] == "Telecommunications"
    assert categories["Vodacom Pty Ltd"] == "Telecommunications"
    assert categories["Shell Ultra City"] == "Auto & Fuel"


def test_process_reconciliation_tolerates_sign_difference(recon_engine, recon_workspace):
    bank = _write_csv(
        recon_workspace, "bank.csv",
        "date,description,amount\n2025-01-01,Acme Corp,-100.00\n",
    )
    invoice = _write_csv(
        recon_workspace, "invoice.csv",
        "date,description,amount\n2025-01-01,Acme Corp,100.00\n",
    )
    results = recon_engine.process_reconciliation(_Upload(bank), _Upload(invoice))
    assert results["summary"]["matched_count"] == 1
    assert results["matched_transactions"][0]["bank_amount"] == -100.0
    assert results["matched_transactions"][0]["inv_amount"] == 100.0


def test_process_reconciliation_flags_amount_mismatch(recon_engine, recon_workspace):
    bank = _write_csv(
        recon_workspace, "bank.csv",
        "date,description,amount\n2025-01-01,Acme Corp,-100.00\n",
    )
    invoice = _write_csv(
        recon_workspace, "invoice.csv",
        "date,description,amount\n2025-01-01,Acme Corp,250.00\n",
    )
    results = recon_engine.process_reconciliation(_Upload(bank), _Upload(invoice))

    assert results["summary"]["matched_count"] == 0
    assert results["summary"]["match_rate"] == 0.0
    assert len(results["unmatched_bank"]) == 1
    assert results["unmatched_bank"][0]["reason"] == "Amount Mismatch"
    assert results["unmatched_bank"][0]["inv_amount"] == 250.0


def test_process_reconciliation_5_percent_tolerance_is_exclusive(recon_engine, recon_workspace):
    # A 5% difference is *not* accepted: the check is a strict `<`.
    bank = _write_csv(
        recon_workspace, "bank.csv",
        "date,description,amount\n2025-01-01,Acme Corp,-105.00\n",
    )
    invoice = _write_csv(
        recon_workspace, "invoice.csv",
        "date,description,amount\n2025-01-01,Acme Corp,100.00\n",
    )
    results = recon_engine.process_reconciliation(_Upload(bank), _Upload(invoice))
    assert results["summary"]["matched_count"] == 0
    assert results["unmatched_bank"][0]["reason"] == "Amount Mismatch"


def test_process_reconciliation_4_percent_difference_is_accepted(recon_engine, recon_workspace):
    bank = _write_csv(
        recon_workspace, "bank.csv",
        "date,description,amount\n2025-01-01,Acme Corp,-100.00\n",
    )
    invoice = _write_csv(
        recon_workspace, "invoice.csv",
        "date,description,amount\n2025-01-01,Acme Corp,104.00\n",
    )
    results = recon_engine.process_reconciliation(_Upload(bank), _Upload(invoice))
    assert results["summary"]["matched_count"] == 1


def test_process_reconciliation_reports_unmatched_on_both_sides(recon_engine, recon_workspace):
    bank = _write_csv(
        recon_workspace, "bank.csv",
        "date,description,amount\n2025-01-05,Ghost Vendor,-50.00\n",
    )
    invoice = _write_csv(
        recon_workspace, "invoice.csv",
        "date,description,amount\n2025-01-09,Missing Inv,20.00\n",
    )
    results = recon_engine.process_reconciliation(_Upload(bank), _Upload(invoice))

    assert results["matched_transactions"] == []
    assert len(results["unmatched_bank"]) == 1
    assert results["unmatched_bank"][0]["reason"] == "Low Description Match"
    assert len(results["unmatched_invoices"]) == 1
    assert results["unmatched_invoices"][0]["status"] == "Unmatched (No Bank Entry)"


def test_process_reconciliation_deduplicates_identical_bank_rows(recon_engine, recon_workspace):
    bank = _write_csv(
        recon_workspace, "bank.csv",
        "date,description,amount\n"
        "2025-01-01,Acme Corp,-100.00\n"
        "2025-01-02,Acme Corp,-100.00\n",
    )
    invoice = _write_csv(
        recon_workspace, "invoice.csv",
        "date,description,amount\n2025-01-01,Acme Corp,100.00\n",
    )
    results = recon_engine.process_reconciliation(_Upload(bank), _Upload(invoice))
    assert results["summary"]["total_bank"] == 1
    assert results["summary"]["matched_count"] == 1


def test_process_reconciliation_filters_noise_rows(recon_engine, recon_workspace):
    bank = _write_csv(
        recon_workspace, "bank.csv",
        "date,description,amount\n"
        "2025-01-01,Opening Balance,-100.00\n"
        "2025-01-02,Acme Corp,-100.00\n",
    )
    invoice = _write_csv(
        recon_workspace, "invoice.csv",
        "date,description,amount\n2025-01-02,Acme Corp,100.00\n",
    )
    results = recon_engine.process_reconciliation(_Upload(bank), _Upload(invoice))
    assert results["summary"]["total_bank"] == 1
    assert results["summary"]["matched_count"] == 1


def test_process_reconciliation_errors_when_only_noise_rows(recon_engine, recon_workspace):
    bank = _write_csv(
        recon_workspace, "bank.csv",
        "date,description,amount\n2025-01-01,Opening Balance,-100.00\n",
    )
    invoice = _write_csv(
        recon_workspace, "invoice.csv",
        "date,description,amount\n2025-01-02,Acme Corp,100.00\n",
    )
    results = recon_engine.process_reconciliation(_Upload(bank), _Upload(invoice))
    assert results["summary"] == {"error": "No valid data rows after filtering noise."}


def test_process_reconciliation_errors_when_descriptions_are_blank(recon_engine, recon_workspace):
    bank = _write_csv(
        recon_workspace, "bank.csv",
        "date,description,amount\n2025-01-01,,-100.00\n",
    )
    invoice = _write_csv(
        recon_workspace, "invoice.csv",
        "date,description,amount\n2025-01-02,Acme Corp,100.00\n",
    )
    results = recon_engine.process_reconciliation(_Upload(bank), _Upload(invoice))
    assert results["summary"] == {"error": "No valid data rows after cleaning."}


def test_process_reconciliation_requires_both_files(recon_engine, recon_workspace):
    results = recon_engine.process_reconciliation(None, None)
    assert results["summary"] == {
        "error": "Please upload both a Bank Statement and an Invoice file."
    }
    assert results["matched_transactions"] == []


def test_process_reconciliation_rejects_unsupported_file_type(recon_engine, recon_workspace):
    unsupported = recon_workspace / "notes.txt"
    unsupported.write_text("hello", encoding="utf-8")
    invoice = _write_csv(
        recon_workspace, "invoice.csv",
        "date,description,amount\n2025-01-01,Acme Corp,100.00\n",
    )
    results = recon_engine.process_reconciliation(_Upload(unsupported), _Upload(invoice))
    assert "Unsupported file format" in results["summary"]["error"]


def test_process_reconciliation_handles_missing_date_column(recon_engine, recon_workspace):
    bank = _write_csv(
        recon_workspace, "bank.csv",
        "description,amount\nAcme Corp,-100.00\n",
    )
    invoice = _write_csv(
        recon_workspace, "invoice.csv",
        "description,amount\nAcme Corp,100.00\n",
    )
    results = recon_engine.process_reconciliation(_Upload(bank), _Upload(invoice))
    assert results["summary"]["matched_count"] == 1
    assert results["matched_transactions"][0]["bank_date"] == ""


def test_process_reconciliation_handles_uppercase_headers(recon_engine, recon_workspace):
    bank = _write_csv(
        recon_workspace, "bank.csv",
        "DATE,DESCRIPTION,AMOUNT\n2025-01-01,Acme Corp,-100.00\n",
    )
    invoice = _write_csv(
        recon_workspace, "invoice.csv",
        "DATE,DESCRIPTION,AMOUNT\n2025-01-01,Acme Corp,100.00\n",
    )
    results = recon_engine.process_reconciliation(_Upload(bank), _Upload(invoice))
    assert results["summary"]["matched_count"] == 1
    assert results["matched_transactions"][0]["match_method"] == "Canonical Match"


def test_process_reconciliation_writes_csv_and_pdf(recon_engine, recon_workspace):
    bank = _write_csv(
        recon_workspace, "bank.csv",
        "date,description,amount\n2025-01-01,Acme Corp,-100.00\n",
    )
    invoice = _write_csv(
        recon_workspace, "invoice.csv",
        "date,description,amount\n2025-01-01,Acme Corp,100.00\n",
    )
    results = recon_engine.process_reconciliation(_Upload(bank), _Upload(invoice))

    csv_path = Path(results["csv_file"])
    pdf_path = Path(results["pdf_file"])
    assert csv_path.exists()
    assert pdf_path.exists()
    # The engine writes relative to the CWD, which the fixture pinned to tmp_path.
    assert csv_path.resolve().parent == recon_workspace.resolve()
    assert pdf_path.resolve().parent == recon_workspace.resolve()
    assert pdf_path.read_bytes().startswith(b"%PDF")

    csv_text = csv_path.read_text(encoding="utf-8")
    assert "Matched" in csv_text
    assert "Acme Corp" in csv_text
    assert results["summary"]["csv_file"] == results["csv_file"]
    assert results["summary"]["pdf_file"] == results["pdf_file"]


def test_process_reconciliation_records_threshold_and_tolerance(recon_engine, recon_workspace):
    bank = _write_csv(
        recon_workspace, "bank.csv",
        "date,description,amount\n2025-01-01,Acme Corp,-100.00\n",
    )
    invoice = _write_csv(
        recon_workspace, "invoice.csv",
        "date,description,amount\n2025-01-01,Acme Corp,100.00\n",
    )
    results = recon_engine.process_reconciliation(
        _Upload(bank), _Upload(invoice), threshold=90, amount_tolerance=0.5
    )
    assert results["summary"]["threshold_used"] == 90
    assert results["summary"]["tolerance_used"] == 50.0
    assert results["summary"]["matched_count"] == 1


def test_process_reconciliation_result_shape(recon_engine, recon_workspace):
    bank = _write_csv(
        recon_workspace, "bank.csv",
        "date,description,amount\n2025-01-01,Acme Corp,-100.00\n",
    )
    invoice = _write_csv(
        recon_workspace, "invoice.csv",
        "date,description,amount\n2025-01-01,Acme Corp,100.00\n",
    )
    results = recon_engine.process_reconciliation(_Upload(bank), _Upload(invoice))

    assert set(results) == {
        "matched_transactions",
        "unmatched_bank",
        "unmatched_invoices",
        "summary",
        "csv_file",
        "pdf_file",
    }
    assert set(results["matched_transactions"][0]) == {
        "bank_date",
        "bank_desc",
        "bank_amount",
        "inv_desc",
        "inv_amount",
        "match_score",
        "status",
        "category",
        "match_method",
    }
    assert results["matched_transactions"][0]["status"] == "Matched"
    assert results["matched_transactions"][0]["match_score"] == 100


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

def test_module_constants(recon_engine):
    assert recon_engine.DEFAULT_THRESHOLD == 75
    assert recon_engine.AMOUNT_TOLERANCE == 0.05
    assert isinstance(recon_engine.COMPANY_NAME, str)
    assert recon_engine.COMPANY_NAME


def test_importing_recon_engine_does_not_launch_gradio(recon_engine):
    """Importing the module must not build or launch the Gradio UI."""
    assert hasattr(recon_engine, "create_ui")
    assert callable(recon_engine.create_ui)
    # ``demo`` only exists once the app is actually launched.
    assert not hasattr(recon_engine, "demo")


def test_repo_modules_are_not_duplicated(recon_engine, vendor_normalizer, vendor_aliases):
    import sys

    assert sys.modules["recon_engine"] is recon_engine
    assert sys.modules["vendor_normalizer"] is vendor_normalizer
    assert sys.modules["vendor_aliases"] is vendor_aliases


def test_no_stray_output_files_in_repo_root(recon_engine, recon_workspace, repo_root):
    """The engine must not litter the repository directory with output files."""
    before = {p.name for p in repo_root.iterdir() if p.name.startswith(("recon_data_", "recon_report_"))}
    bank = _write_csv(
        recon_workspace, "bank.csv",
        "date,description,amount\n2025-01-01,Acme Corp,-100.00\n",
    )
    invoice = _write_csv(
        recon_workspace, "invoice.csv",
        "date,description,amount\n2025-01-01,Acme Corp,100.00\n",
    )
    recon_engine.process_reconciliation(_Upload(bank), _Upload(invoice))
    after = {p.name for p in repo_root.iterdir() if p.name.startswith(("recon_data_", "recon_report_"))}
    assert before == after
    assert os.getcwd() == str(recon_workspace)
