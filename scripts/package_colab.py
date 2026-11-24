"""Package the frozen M18 inputs and generate the GPU notebook."""
import argparse
import json
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eval.heldout import load_cases, verify_training
from eval.train_release_adapter import BASE_REVISION


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/colab")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cases = load_cases()
    training = verify_training(ROOT, cases)
    members = [
        "agriagent/__init__.py", "agriagent/model.py", "data/train/examples.jsonl",
        "eval/__init__.py", "eval/heldout.py", "eval/m18_cases.json",
        "eval/requirements-colab.txt", "eval/train_release_adapter.py",
        *[case["input"] for case in cases], *[example["source"] for example in training],
    ]
    with ZipFile(args.output / "agriagent-colab-inputs.zip", "x", compression=ZIP_DEFLATED) as bundle:
        for name in members:
            bundle.write(ROOT / name, name)
    cells = [
        ("markdown", "# AgriAgent M18\n\nSelect a GPU runtime, run cells in order, and upload the generated input ZIP. "
         "The output ZIP contains predictions, logs and PEFT weights. Held-out reference answers remain local."),
        ("code", "from google.colab import files\nfrom pathlib import Path\nfrom zipfile import ZipFile\n"
         "uploaded = files.upload()\narchive, = uploaded\n"
         "with ZipFile(archive) as f:\n"
         "    for name in f.namelist():\n"
         "        p = Path(name)\n"
         "        if p.is_absolute() or '..' in p.parts: raise ValueError(name)\n"
         "    f.extractall()"),
        ("code", "%pip install -r eval/requirements-colab.txt"),
        ("code", "import subprocess, sys\nsubprocess.run([sys.executable, 'eval/train_release_adapter.py', "
         f"'--revision', '{BASE_REVISION}'], check=True)"),
        ("code", "import shutil\narchive = shutil.make_archive('agriagent-m18-results', 'zip', 'output', 'm18')\n"
         "files.download(archive)"),
    ]
    notebook = {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {"accelerator": "GPU", "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "cells": [
            {"id": f"agri-{i}", "cell_type": kind, "metadata": {}, "source": text.splitlines(keepends=True),
             **({"execution_count": None, "outputs": []} if kind == "code" else {})}
            for i, (kind, text) in enumerate(cells)
        ],
    }
    with (args.output / "AgriAgent_M18.ipynb").open("x", encoding="utf-8") as stream:
        json.dump(notebook, stream, indent=2)
    print(args.output)


if __name__ == "__main__":
    main()
