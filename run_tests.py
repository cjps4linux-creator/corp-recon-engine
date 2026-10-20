#!/usr/bin/env python3
"""
Test runner for reconEngine - processes all test datasets and verifies results
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from recon_engine import process_reconciliation

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")

datasets = [
    {
        "name": "Company 1 - Market Data & Custody Providers",
        "bank": os.path.join(TEST_DATA_DIR, "company1_bank_statement.csv"),
        "invoices": os.path.join(TEST_DATA_DIR, "company1_invoices.csv"),
        "expected_match_rate": 100.0,
    },
    {
        "name": "Company 2 - Asset Managers & Fund Complexes",
        "bank": os.path.join(TEST_DATA_DIR, "company2_bank_statement.csv"),
        "invoices": os.path.join(TEST_DATA_DIR, "company2_invoices.csv"),
        "expected_match_rate": 100.0,
    },
    {
        "name": "Company 3 - HFT/Prop Trading Firms & Prime Brokers",
        "bank": os.path.join(TEST_DATA_DIR, "company3_bank_statement.csv"),
        "invoices": os.path.join(TEST_DATA_DIR, "company3_invoices.csv"),
        "expected_match_rate": 100.0,
    },
    {
        "name": "Company 4 - Fuzzy Matching Test (name variations, extra items)",
        "bank": os.path.join(TEST_DATA_DIR, "company4_fuzzy_bank.csv"),
        "invoices": os.path.join(TEST_DATA_DIR, "company4_fuzzy_invoices.csv"),
        "expected_match_rate": 75.0,  # Realistic for name variations
    },
]

def run_test(dataset):
    print(f"\n{'='*70}")
    print(f"TEST: {dataset['name']}")
    print(f"{'='*70}")
    
    # Load files as file-like objects
    class FileObj:
        def __init__(self, path):
            self.name = path
    
    bank_file = FileObj(dataset["bank"])
    inv_file = FileObj(dataset["invoices"])
    
    results = process_reconciliation(bank_file, inv_file)
    
    if results["summary"].get("error"):
        print(f"❌ ERROR: {results['summary']['error']}")
        return False
    
    s = results["summary"]
    print(f"Total Bank Items:     {s['total_bank']}")
    print(f"Total Invoices:       {s['total_invoice']}")
    print(f"Matched:              {s['matched_count']}")
    print(f"Unmatched (Bank):     {s['unmatched_bank_count']}")
    print(f"Unmatched (Invoice):  {s['unmatched_inv_count']}")
    print(f"Match Rate:           {s['match_rate']}%")
    print(f"Threshold Used:       {s['threshold_used']}%")
    print(f"Tolerance Used:       {s['tolerance_used']}%")
    print(f"PDF Report:           {s['pdf_file']}")
    print(f"CSV Export:           {s['csv_file']}")
    
    # Show unmatched details
    if results["unmatched_bank"]:
        print("\n⚠️  UNMATCHED BANK ITEMS:")
        for u in results["unmatched_bank"]:
            print(f"   - {u['bank_date']} | {u['bank_desc']} | {u['bank_amount']:,.2f} | Reason: {u['reason']}")
    
    if results["unmatched_invoices"]:
        print("\n⚠️  UNMATCHED INVOICES:")
        for u in results["unmatched_invoices"]:
            print(f"   - {u['inv_date']} | {u['inv_desc']} | {u['inv_amount']:,.2f}")
    
    # Verify against expected
    passed = s['match_rate'] >= dataset['expected_match_rate']
    if passed:
        print(f"\n✅ PASS - Match rate {s['match_rate']}% >= {dataset['expected_match_rate']}%")
    else:
        print(f"\n❌ FAIL - Match rate {s['match_rate']}% < {dataset['expected_match_rate']}%")
    
    return passed

if __name__ == "__main__":
    print("🧪 reconEngine Test Suite")
    print("=" * 70)
    
    all_passed = True
    for ds in datasets:
        passed = run_test(ds)
        all_passed = all_passed and passed
    
    print(f"\n{'='*70}")
    if all_passed:
        print("🎉 ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print(f"{'='*70}")
    
    sys.exit(0 if all_passed else 1)