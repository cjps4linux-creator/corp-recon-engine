"""Tests for ``vendor_normalizer`` and ``vendor_aliases``.

Both modules are deliberately light: ``vendor_normalizer`` imports only ``re``
and ``vendor_aliases`` imports only ``pandas``, so these tests never touch the
Gradio UI, the network, or the filesystem.

All expected values were verified by executing the modules against the
repository's own virtualenv.
"""

from __future__ import annotations

import math

import pytest


# ---------------------------------------------------------------------------
# normalize_vendor_name
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # Falsy input yields an empty string.
        ("", ""),
        (None, ""),
        ("   ", ""),
        ("\t\n", ""),
        # Case folding and surrounding whitespace.
        ("  MTN South Africa  ", "mtn south africa"),
        ("ACME, Inc.", "acme"),
        # Generic corporate suffixes are dropped.
        ("Acme Corp", "acme"),
        ("Acme Inc.", "acme"),
        ("Acme Corporation", "acme"),
        ("Acme Corporation Ltd", "acme"),
        ("Woolworths (Pty) Ltd", "woolworths"),
        ("Sasol Limited", "sasol"),
        ("Acme PTY", "acme"),
        ("Acme LLC", "acme"),
        ("Acme PLC", "acme"),
        ("Acme GMBH", "acme"),
        ("Acme SARL", "acme"),
        ("Acme BV", "acme"),
        ("Acme NV", "acme"),
        ("Acme LLP", "acme"),
        ("Acme LP", "acme"),
        # A name made only of suffixes normalises to nothing.
        ("Co Ltd", ""),
        ("SA Company", ""),
        ("Company Ltd", ""),
        # Pure-number tokens are dropped.
        ("123", ""),
        ("123 456", ""),
        ("Apple 42 Inc", "apple"),
        # "42abc" is not a pure number, so it survives.
        ("42abc", "42abc"),
        # Punctuation becomes a space; underscores are kept (they are \w).
        ("A-B_C", "a b_c"),
        ("Nando's", "nando s"),
        # Unicode letters survive normalisation.
        ("Ünïcödé Ltd", "ünïcödé"),
        ("Café S.A.", "café s a"),
        # Suffixes not in the generic set are kept.
        ("Acme Holdings", "acme holdings"),
        ("Acme Corporate", "acme corporate"),
        ("Included Ltd", "included"),
        # Repeated whitespace is collapsed by the token join.
        ("Acme  Co", "acme"),
    ],
)
def test_normalize_vendor_name(vendor_normalizer, value, expected):
    assert vendor_normalizer.normalize_vendor_name(value) == expected


def test_normalize_vendor_name_requires_a_string(vendor_normalizer):
    with pytest.raises(AttributeError):
        vendor_normalizer.normalize_vendor_name(123)
    with pytest.raises(AttributeError):
        vendor_normalizer.normalize_vendor_name(4.5)


def test_normalize_vendor_name_does_not_apply_typo_corrections(vendor_normalizer):
    """``TYPO_CORRECTIONS`` is defined but never applied by the normaliser."""
    assert vendor_normalizer.normalize_vendor_name("mineing") == "mineing"
    assert vendor_normalizer.normalize_vendor_name("sollutions") == "sollutions"
    assert vendor_normalizer.normalize_vendor_name("Pick n Payy") == "pick n payy"


def test_typo_corrections_table_is_populated(vendor_normalizer):
    assert isinstance(vendor_normalizer.TYPO_CORRECTIONS, dict)
    assert vendor_normalizer.TYPO_CORRECTIONS["payy"] == "pay"
    assert vendor_normalizer.TYPO_CORRECTIONS["mineing"] == "mining"


# ---------------------------------------------------------------------------
# normalize_description_for_matching
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("", ""),
        (None, ""),
        # Every supported bank-transaction prefix is stripped.
        ("Payment to Acme Corp", "acme"),
        ("payment from Amazon", "amazon"),
        ("Transfer to MTN", "mtn"),
        ("Transfer from Standard Bank", "standard bank"),
        ("Debit card Woolworths", "woolworths"),
        ("Credit card Netflix", "netflix"),
        ("Card payment Shell", "shell"),
        ("Direct debit Eskom", "eskom"),
        ("Standing order Sasol", "sasol"),
        ("Online payment Uber", "uber"),
        ("Mobile payment Vodacom", "vodacom"),
        ("POS purchase Pick n Pay", "pick n pay"),
        ("ATM withdrawal Nedbank", "nedbank"),
        ("Cash withdrawal FNB", "fnb"),
        ("Bill payment Eskom", "eskom"),
        ("Invoice payment Quickbooks", "quickbooks"),
        ("Vendor payment Acme", "acme"),
        # Case-insensitive and whitespace-tolerant.
        ("Payment To Acme Corp", "acme"),
        ("Payment to  Acme", "acme"),
        ("payment  to   acme", "acme"),
        # Numeric tokens inside the description are dropped.
        ("Payment to 123 Acme", "acme"),
        # A prefix is only removed when it is a *prefix*.
        ("Acme Payment to", "acme payment to"),
        ("POS purchase to Shell", "to shell"),
        # Only the first matching prefix is removed.
        ("Payment to payment to acme", "payment to acme"),
        # Descriptions that merely start with a prefix word are untouched.
        ("Payment", "payment"),
        ("to Acme", "to acme"),
        # A description that is only a prefix collapses to an empty string.
        ("Payment to", ""),
        ("Payment to ", ""),
        ("card payment", ""),
    ],
)
def test_normalize_description_for_matching(vendor_normalizer, value, expected):
    assert vendor_normalizer.normalize_description_for_matching(value) == expected


def test_normalize_description_requires_a_string(vendor_normalizer):
    with pytest.raises(AttributeError):
        vendor_normalizer.normalize_description_for_matching(123)


def test_normalize_description_starts_from_normalize_vendor_name(vendor_normalizer):
    assert vendor_normalizer.normalize_description_for_matching("Acme Corp") == (
        vendor_normalizer.normalize_vendor_name("Acme Corp")
    )


# ---------------------------------------------------------------------------
# get_canonical_name
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # Empty / missing input yields an empty string.
        ("", ""),
        (None, ""),
        (float("nan"), ""),
        # Known aliases resolve to their canonical name.
        ("AWS", "amazon web services"),
        ("aws", "amazon web services"),
        ("  AWS  ", "amazon web services"),
        ("Amazon Web Services", "amazon web services"),
        ("GitHub Organizations", "github inc"),
        ("Pick n Payy", "pick n pay"),
        ("Vodacome", "vodacom"),
        ("eskom", "eskom holdings soc"),
        ("marriott intl", "marriott international"),
        ("anglo amercan", "anglo american"),
        ("exarro", "exxaro"),
        ("saa", "south african airways"),
        ("wartsila", "wärtsilä"),
        ("Canadian solar", "canadian solar"),
        # Unknown names come back lowercased and stripped.
        ("Some Random Co", "some random co"),
        ("nonexistent vendor 123", "nonexistent vendor 123"),
        ("Nando's", "nando's"),
    ],
)
def test_get_canonical_name(vendor_aliases, value, expected):
    assert vendor_aliases.get_canonical_name(value) == expected


def test_get_canonical_name_is_case_insensitive(vendor_aliases):
    assert vendor_aliases.get_canonical_name("AWS") == vendor_aliases.get_canonical_name("aws")


def test_get_canonical_name_returns_lowercase_for_unknown(vendor_aliases):
    result = vendor_aliases.get_canonical_name("Totally Unknown Vendor")
    assert result == "totally unknown vendor"


def test_get_canonical_name_handles_non_string_input(vendor_aliases):
    # [lorem]-string, [lorem]-nullable values are coerced through str().
    assert vendor_aliases.get_canonical_name(123) == "123"


def test_get_canonical_name_rejects_pd_na(vendor_aliases):
    import pandas as pd

    with pytest.raises(TypeError):
        vendor_aliases.get_canonical_name(pd.NA)


def test_get_canonical_name_handles_pandas_nat(vendor_aliases):
    import pandas as pd

    assert vendor_aliases.get_canonical_name(pd.NaT) == ""


# ---------------------------------------------------------------------------
# Alias map integrity
# ---------------------------------------------------------------------------

def test_all_aliases_is_the_union_of_the_per_company_maps(vendor_aliases):
    per_company = [
        vendor_aliases.NEXUS_ALIASES,
        vendor_aliases.MULLER_ALIASES,
        vendor_aliases.OASIS_ALIASES,
        vendor_aliases.KHUMALO_ALIASES,
        vendor_aliases.VERDANT_ALIASES,
    ]
    total = sum(len(m) for m in per_company)
    assert len(vendor_aliases.ALL_ALIASES) == total
    for alias_map in per_company:
        for key, value in alias_map.items():
            assert vendor_aliases.ALL_ALIASES[key] == value


def test_all_alias_values_are_lowercase_strings(vendor_aliases):
    for value in vendor_aliases.ALL_ALIASES.values():
        assert isinstance(value, str)
        assert value == value.lower()


def test_alias_map_contains_expected_entries(vendor_aliases):
    aliases = vendor_aliases.ALL_ALIASES
    assert aliases["aws"] == "amazon web services"
    assert aliases["pick n payy"] == "pick n pay"
    assert aliases["eskom holdings soc"] == "eskom holdings soc"
    assert aliases["exxaro"] == "exxaro"
    assert aliases["siemens ag"] == "siemens"


def test_alias_map_has_an_unreachable_whitespace_padded_key(vendor_aliases):
    """A real data defect: one key carries a leading space and is unreachable.

    ``get_canonical_name`` strips the input before looking it up, so the
    ``" Eaton corporation"`` key can never be hit by any lookup.
    """
    assert " Eaton corporation" in vendor_aliases.ALL_ALIASES
    assert "eaton corporation" not in vendor_aliases.ALL_ALIASES
    assert vendor_aliases.get_canonical_name("Eaton Corporation") == "eaton corporation"
    assert vendor_aliases.get_canonical_name("Eaton") == "eaton"


def test_alias_canonical_values_that_are_not_themselves_keys(vendor_aliases):
    """Real data defect: three canonical targets are not reachable as keys.

    * ``south african airways`` is produced by the key ``"south African
      airways"``, which carries an embedded capital A and therefore never
      matches a lower-cased lookup.
    * ``telkom sa`` and ``vodacom`` are produced by ``telkom sa soc`` and
      ``vodacom sa`` but have no key of their own.
    """
    unreachable = sorted(
        {value for value in vendor_aliases.ALL_ALIASES.values()}
        - set(vendor_aliases.ALL_ALIASES)
    )
    assert unreachable == ["south african airways", "telkom sa", "vodacom"]

    # "South African Airways" therefore does NOT resolve to the canonical name.
    assert vendor_aliases.get_canonical_name("South African Airways") == (
        "south african airways"
    )
    assert vendor_aliases.get_canonical_name("saa") == "south african airways"
    assert vendor_aliases.get_canonical_name("telkom sa") == "telkom sa"
    assert vendor_aliases.get_canonical_name("vodacom") == "vodacom"


def test_alias_map_keys_are_mostly_lowercase(vendor_aliases):
    """Only three keys carry stray capitalisation."""
    mixed_case = sorted(key for key in vendor_aliases.ALL_ALIASES if key != key.lower())
    assert mixed_case == [" Eaton corporation", "Canadian solar", "south African airways"]


def test_alias_map_has_no_nan_targets(vendor_aliases):
    for value in vendor_aliases.ALL_ALIASES.values():
        assert not (isinstance(value, float) and math.isnan(value))
