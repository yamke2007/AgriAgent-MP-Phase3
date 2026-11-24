import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from agriagent.forecast_ocr import observations
from agriagent.public_sources import des_district_tables, machinery
from scripts.import_lgd import registry_from_csv
from scripts.verify_source_expansion import automation


class SourceExpansionTests(unittest.TestCase):
    def test_m12_includes_failed_partial_and_historically_manual_inputs(self):
        cases = [
            {"status": "complete", "manual_interventions": 0},
            {"status": "complete", "manual_interventions": 1},
            {"status": "partial", "manual_interventions": 0},
            {"status": "failed", "manual_interventions": 0},
        ]
        report = automation(cases)
        self.assertEqual(report["attempted"], 4)
        self.assertEqual(report["value"], 0.25)
        self.assertEqual(automation(cases, include_upstream_manual=False)["value"], 0.5)

    def test_subsidy_parser_ignores_separate_loan_amount(self):
        fixture = BeautifulSoup("""
        <div id="collapseOne3">
          <li>जनजाति के आवेदकों को लागत का 50 प्रतिशत अधिकतम राशि रू. 11 लाख</li>
          <li>अधिकतम राशि रू. 25 लाख तक का ऋण</li>
        </div>""", "html.parser")
        records, _ = machinery(fixture)
        amounts = {row["variable"]: row["value"] for row in records}
        self.assertEqual(amounts["custom_hiring_subsidy_cap_lakh_inr"], "11")

    def test_des_apy_preserves_missing_cells_and_financial_year(self):
        rows = [
            ["State/Crop/District", "Year", "Season", "Area (Hectare)", "Production (Tonne)", "Yield (Tonne/Hectare)"],
            ["Madhya Pradesh", "", "", "", "", ""],
            ["1. Maize", "", "", "", "", ""],
            ["1. Anuppur", "2019 - 2020", "Summer", "30", "", ""],
        ]
        records, warnings = des_district_tables([dict(page=1, table=1, rows=rows)], "", "apy")
        self.assertEqual([(r["variable"], r["value"], r["period"]) for r in records], [("area", "30", "2019-20")])
        self.assertIn("2 APY cells", warnings[0])
        rows[0][-2] = "Production (Kilograms)"
        self.assertFalse(des_district_tables([dict(page=1, table=1, rows=rows)], "", "apy")[0])

    def test_unreadable_forecast_date_is_not_inferred(self):
        rows = [["Parameter", "2026-11-24", "", "2026-11-26", "2026-11-27", "2026-11-28"],
                ["Rainfall(mm)", "0", "1", "0", "0", "0"]]
        records, messages = observations(rows, "Sehore", "2026-11-23", 1)
        self.assertEqual(records, [])
        self.assertIn("headers", messages[0])

    def test_lgd_requires_a_state_and_rejects_conflicting_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "districts.csv"
            path.write_text("stateCode,stateNameEnglish,districtCode,districtNameEnglish\n"
                            "23,Madhya Pradesh,427,Sehore\n"
                            "22,Chhattisgarh,433,Durg\n", encoding="utf-8")
            self.assertEqual(registry_from_csv(path), {"427": "Sehore"})
            path.write_text("District Code,District Name\n427,Sehore\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "MP-only export"):
                registry_from_csv(path)
            path.write_text("State Code,District Code,District Name\n"
                            "23,123,Hoshangabad\n23,456,Narmadapuram\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Conflicting district"):
                registry_from_csv(path)


if __name__ == "__main__":
    unittest.main()
