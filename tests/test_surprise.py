import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from agriagent.pipeline import sha
from eval.run_surprise import score_saved


class SurpriseScoringTests(unittest.TestCase):
    def test_scores_saved_outputs_and_rejects_changed_run(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "runs").mkdir()
            record = dict(crop="wheat", location="sehore", period="2022",
                          variable="production", value="42", unit="tonne", value_kind="integer")
            report = {"cases": []}
            key = []
            for index in range(3):
                run = {"run_id": str(index), "input_sha256": str(index), "records": [record]}
                path = output / "runs" / f"{index}.json"
                path.write_text(json.dumps(run), encoding="utf-8")
                report["cases"].append({"run_id": str(index), "input_sha256": str(index), "run_sha256": sha(path)})
                key.append({"records": [record], "input_sha256": str(index)})
            with redirect_stdout(StringIO()):
                score_saved(output, report, key)
            result = json.loads((output / "surprise-scored.json").read_text(encoding="utf-8"))
            self.assertEqual((result["tp"], result["fp"], result["fn"], result["f1"]), (3, 0, 0, 1.0))
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Saved run changed"):
                score_saved(output, report, key)
