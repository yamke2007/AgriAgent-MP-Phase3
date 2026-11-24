"""Run three unseen instructor inputs with an optional independently checked key."""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agriagent.pipeline import process, sha
from eval.matching import counts, f1


def checked_key(parser, path):
    key = json.loads(path.read_text(encoding="utf-8-sig"))
    if (not isinstance(key, list) or len(key) != 3 or
            not all(isinstance(item, dict) and isinstance(item.get("records"), list)
                    and 10 <= len(item["records"]) <= 15 and isinstance(item.get("language"), str)
                    for item in key) or not any(item["language"].casefold().split("-")[0] != "en" for item in key)):
        parser.error("Use three checked keys of 10–15 fields, with at least one non-English input")
    return key


def score_saved(output, report, key):
    report["status"] = "scored_with_supplied_key"
    totals = [0, 0, 0]
    agents, groups = defaultdict(list), defaultdict(list)
    for row, reference in zip(report["cases"], key, strict=True):
        path = output / "runs" / (row["run_id"] + ".json")
        if sha(path) != row["run_sha256"]:
            raise ValueError("Saved run changed: " + row["run_id"])
        run = json.loads(path.read_text(encoding="utf-8"))
        if run["input_sha256"] != row["input_sha256"] or run["run_id"] != row["run_id"]:
            raise ValueError("Saved run does not match the captured input")
        if reference.get("input_sha256", row["input_sha256"]) != row["input_sha256"]:
            raise ValueError("Answer key hash does not match the input order")
        scores = counts(run["records"], reference["records"])
        row.update(tp=scores[0], fp=scores[1], fn=scores[2], f1=f1(*scores))
        row["agent"] = reference.get("agent", run.get("agent", "unrouted"))
        row["source_group"] = reference.get("source_group", run.get("source_type", "unknown"))
        agents[row["agent"]].append(scores)
        groups[row["source_group"]].append(scores)
        totals = [a + b for a, b in zip(totals, scores, strict=True)]
    report.update(tp=totals[0], fp=totals[1], fn=totals[2], f1=f1(*totals))
    for label, scopes in (("per_agent", agents), ("per_source_group", groups)):
        report[label] = {}
        for scope, scores in scopes.items():
            tp, fp, fn = map(sum, zip(*scores, strict=True))
            report[label][scope] = dict(tp=tp, fp=fp, fn=fn, cases=len(scores), f1=f1(tp, fp, fn))
    report["macro_agents_f1"] = sum(scope["f1"] for scope in report["per_agent"].values()) / len(agents)
    text = json.dumps(report, indent=2, ensure_ascii=True)
    with (output / "surprise-scored.json").open("x", encoding="utf-8") as file:
        file.write(text + "\n")
    print(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, nargs="*")
    parser.add_argument("--key", type=Path, help="JSON list of three {language, records} entries, in input order")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--score-existing", action="store_true", help="score a captured run without reprocessing")
    parser.add_argument("--manual-interventions", nargs=3, type=int, default=(0, 0, 0))
    args = parser.parse_args()
    if any(number < 0 for number in args.manual_interventions):
        parser.error("Manual interventions must be nonnegative")
    output = args.output.resolve()
    if args.score_existing:
        if args.inputs or not args.key or any(args.manual_interventions):
            parser.error("--score-existing requires --key and the capture directory, without inputs or interventions")
        report = json.loads((output / "surprise.json").read_text(encoding="utf-8"))
        score_saved(output, report, checked_key(parser, args.key))
        return
    if len(args.inputs) != 3:
        parser.error("Provide exactly three input paths")
    key = checked_key(parser, args.key) if args.key else None
    if len({path.resolve() for path in args.inputs}) != 3:
        parser.error("Provide three distinct inputs")
    if output.exists() and any(output.iterdir()):
        parser.error("Choose an empty directory")
    config = {"database": str(output / "agriagent.sqlite"), "output_dir": str(output / "runs"),
              "automation_log": str(output / "automation.csv")}
    report = {"cases": [], "metric": "M5", "status": "awaiting_key", "f1": None}
    for path, interventions in zip(args.inputs, args.manual_interventions, strict=True):
        result = process(path, config, manual_interventions=interventions)
        row = {name: result[name] for name in ("input", "run_id", "input_sha256", "status", "errors", "warnings")}
        row["run_sha256"] = sha(output / "runs" / (result["run_id"] + ".json"))
        row["manual_interventions"] = interventions
        report["cases"].append(row)
    text = json.dumps(report, indent=2, ensure_ascii=True)
    (output / "surprise.json").write_text(text + "\n", encoding="utf-8")
    if key:
        score_saved(output, report, key)
    else:
        print(text)


if __name__ == "__main__":
    main()
