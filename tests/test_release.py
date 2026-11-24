import json
import unittest
from pathlib import Path
from unittest.mock import patch

from agriagent.pipeline import ROOT, process
from eval.heldout import load_cases, verify_training
from eval.source_checks import input_support


class ReleaseTests(unittest.TestCase):
    def test_production_csv_preserves_season_and_original_locator(self):
        result = process(ROOT / "data/production/mp_crop_production_2016_2022.csv", persist=False)
        self.assertEqual(result["agent"], "statistics")
        self.assertEqual(len(result["records"]), 3785)
        for row in result["records"]:
            self.assertIn(row["season"], ("kharif", "rabi", "summer"))
            self.assertRegex(row["origin_locator"], r"^csv:line:\d+/column:(Area|Production)$")

    def test_source_support_rejects_another_value_from_same_table_row(self):
        case = load_cases()[0]
        path = ROOT / case["input"]
        result = process(path, persist=False)
        price = next(row for row in result["records"] if row["variable"] == "min_price")
        wrong_column = dict(price, variable="max_price")
        self.assertTrue(input_support(path, price["locator"], "tables", price))
        self.assertFalse(input_support(path, price["locator"], "tables", wrong_column))
        self.assertFalse(input_support(path, price["locator"], "tables", dict(price, location="different")))

    def test_adapter_confirms_exact_inputs_and_preserves_their_locators(self):
        path = ROOT / load_cases()[0]["input"]
        reference = process(path, persist=False)["records"][0]
        hallucination = dict(reference, location="other")
        usage = {"input_tokens": 20, "generated_tokens": 15}
        with patch("agriagent.model.configured_prediction", return_value=([reference, hallucination], usage)):
            result = process(path, {"adapter_path": "mock"}, persist=False)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["records"][0]["locator"], reference["locator"])
        self.assertTrue(result["records"][0]["model_confirmed"])
        self.assertEqual(result["model_usage"], [usage])

    def test_heldout_cohort_lineage(self):
        cases = load_cases()
        self.assertEqual(len(cases), 10)
        self.assertTrue(all(case["split"] == "heldout" for case in cases))
        self.assertEqual(len(verify_training(ROOT, cases)), 72)

    def test_production_query_frozen_examples_cover_protocol_categories(self):
        from agriagent.queries import QUERIES

        expected = json.loads((ROOT / "db/queries_expected.json").read_text(encoding="utf-8"))
        self.assertEqual(set(QUERIES), set(expected))
        for category, minimum in (("spatial", 2), ("temporal", 2), ("provenance", 1)):
            self.assertGreaterEqual(sum(query.category == category for query in QUERIES.values()), minimum)


if __name__ == "__main__":
    unittest.main()
