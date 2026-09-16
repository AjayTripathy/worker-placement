import os
import sys
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from desk.order_executor import (
    resolve_contract_specs,
    validate_order,
    IBKROrderExecutor,
    is_halted,
    HALT_FLAG_PATH,
)


class TestOrderExecutor(unittest.TestCase):

    def test_resolve_contract_specs_tse(self):
        """Verify Japanese TSE equities resolution and 100-lot enforcement."""
        specs = resolve_contract_specs("6626.T")
        self.assertEqual(specs["symbol"], "6626")
        self.assertEqual(specs["exchange"], "SMART")
        self.assertEqual(specs["primaryExchange"], "TSEJ")
        self.assertEqual(specs["currency"], "JPY")
        self.assertEqual(specs["lot_size"], 100)
        self.assertEqual(specs["venue_name"], "TSE")

        # Also test pure numeric 4-digit symbol
        specs2 = resolve_contract_specs("7722")
        self.assertEqual(specs2["symbol"], "7722")
        self.assertEqual(specs2["primaryExchange"], "TSEJ")
        self.assertEqual(specs2["lot_size"], 100)

    def test_resolve_contract_specs_krx(self):
        """Verify Korean KRX equities resolution."""
        specs = resolve_contract_specs("058850.KS")
        self.assertEqual(specs["symbol"], "058850")
        self.assertEqual(specs["currency"], "KRW")
        self.assertEqual(specs["primaryExchange"], "KRX")
        self.assertEqual(specs["lot_size"], 1)

    def test_resolve_contract_specs_lse(self):
        """Verify UK LSE equities resolution (Pence Ordinaries vs USD GDRs)."""
        # Ordinary UK stock in pence
        specs = resolve_contract_specs("GMS.L")
        self.assertEqual(specs["symbol"], "GMS")
        self.assertEqual(specs["currency"], "GBP")
        self.assertEqual(specs["price_unit"], "PENCE_GBX")
        self.assertEqual(specs["primaryExchange"], "LSE")
        self.assertEqual(specs["lot_size"], 1)

        # IOB GDR in USD
        specs_gdr = resolve_contract_specs("HSBK.L")
        self.assertEqual(specs_gdr["symbol"], "HSBK")
        self.assertEqual(specs_gdr["currency"], "USD")
        self.assertEqual(specs_gdr["price_unit"], "USD")
        self.assertEqual(specs_gdr["primaryExchange"], "LSE")

    def test_pence_vs_pound_validation_guard(self):
        """Verify pence vs pound plausibility guard."""
        # 1. Valid pence limit price (20.45p) -> passes
        valid, err, specs = validate_order("GMS.L", "BUY", 10000, 20.45, "DAY")
        self.assertTrue(valid)
        self.assertEqual(err, "VALID")

        # 2. Decimal pound mistake (0.2045 instead of 20.45) -> rejected
        invalid, err2, _ = validate_order("GMS.L", "BUY", 10000, 0.2045, "DAY")
        self.assertFalse(invalid)
        self.assertIn("POTENTIAL PENCE-VS-POUND UNIT ERROR", err2)
        self.assertIn("looks like a GBP decimal", err2)

        # 3. IOB GDR in USD (e.g. HSBK at $44.00) -> passes
        valid_gdr, err3, _ = validate_order("HSBK.L", "BUY", 100, 44.0, "DAY")
        self.assertTrue(valid_gdr)
        self.assertEqual(err3, "VALID")

    def test_resolve_contract_specs_us(self):
        """Verify US equities resolution."""
        specs = resolve_contract_specs("ALAB")
        self.assertEqual(specs["symbol"], "ALAB")
        self.assertEqual(specs["currency"], "USD")
        self.assertEqual(specs["primaryExchange"], "NASDAQ")
        self.assertEqual(specs["lot_size"], 1)


    def test_validate_order_lot_sizes(self):
        """Verify lot size validation guards."""
        # TSE requires multiples of 100
        valid, err, specs = validate_order("6626.T", "BUY", 3700, 2160.0, "DAY")
        self.assertTrue(valid)
        self.assertEqual(err, "VALID")

        # Non-multiple of 100 should fail
        invalid, err2, _ = validate_order("6626.T", "BUY", 3750, 2160.0, "DAY")
        self.assertFalse(invalid)
        self.assertIn("Lot size violation", err2)

    def test_validate_order_sanity_checks(self):
        """Verify price, qty, and action bounds."""
        # Negative limit price
        v1, e1, _ = validate_order("AAPL", "BUY", 10, -50.0)
        self.assertFalse(v1)
        self.assertIn("Limit price must be strictly positive", e1)

        # Zero qty
        v2, e2, _ = validate_order("AAPL", "BUY", 0, 150.0)
        self.assertFalse(v2)
        self.assertIn("Quantity must be positive", e2)

        # Invalid action
        v3, e3, _ = validate_order("AAPL", "HOLD", 10, 150.0)
        self.assertFalse(v3)
        self.assertIn("Invalid action", e3)

        # Invalid TIF
        v4, e4, _ = validate_order("AAPL", "BUY", 10, 150.0, tif="INVALID_TIF")
        self.assertFalse(v4)
        self.assertIn("Invalid TIF", e4)

    def test_order_dry_run_execution(self):
        """Verify dry-run execution validates order and logs audit without broker call."""
        executor = IBKROrderExecutor()
        res = executor.place_limit_order("6626.T", "BUY", 3700, 2160.0, tif="DAY", dry_run=True)
        self.assertEqual(res["status"], "DRY_RUN_PASSED")
        self.assertEqual(res["order_details"]["qty"], 3700)
        self.assertEqual(res["order_details"]["limit_price"], 2160.0)
        self.assertEqual(res["order_details"]["specs"]["currency"], "JPY")

    def test_emergency_halt_guard(self):
        """Verify emergency halt flag blocks all order submissions."""
        try:
            HALT_FLAG_PATH.write_text("TEST HALT")
            self.assertTrue(is_halted())

            valid, err, _ = validate_order("AAPL", "BUY", 10, 150.0)
            self.assertFalse(valid)
            self.assertIn("TRADING IS HALTED", err)
        finally:
            if HALT_FLAG_PATH.exists():
                HALT_FLAG_PATH.unlink()
            self.assertFalse(is_halted())


if __name__ == "__main__":
    unittest.main()
