import hashlib
from pathlib import Path

def audit(root):
    root=Path(root)
    train=root/"data/train"
    files=[p for p in train.rglob("*") if p.is_file() and p.name != "README.md"] if train.exists() else []
    hashes={hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    cases=[p for p in (root/"eval/cases").iterdir() if p.is_file()]
    # Parent-source overlap must also be checked if future training uses raw snapshots.
    overlaps=[str(p.relative_to(root)) for p in cases+list((root/"data/raw").glob("*")) if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() in hashes]
    return dict(training_files=len(files),case_files=len(cases),overlaps=overlaps,
                status="overlap_detected" if overlaps else "no_local_training_files" if not files else "no_exact_hash_overlap",
                limitation=("Exact-hash check of every training file against evaluation inputs and raw parent sources. "
                            "Training examples (if any) come from separately collected sources/years. "
                            "Hashes cannot detect paraphrase/semantic overlap or unknown pretrained corpora."))
