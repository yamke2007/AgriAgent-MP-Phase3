"""Validate that the manually maintained Phase 2 status is present.

Do not regenerate the status document from stale hard-coded snapshots: evaluation
metrics and open gates change as evidence is collected. Update the document only
when the underlying run/evidence has been checked.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    status=ROOT/"docs/phase2_implementation_status.md"
    if not status.is_file() or status.stat().st_size < 1000:
        raise SystemExit("Phase 2 status document missing or incomplete")
    print("Phase 2 status document present; manual evidence-grounded status preserved")
if __name__=="__main__": main()
