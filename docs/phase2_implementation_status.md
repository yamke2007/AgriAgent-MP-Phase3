# Phase 2 implementation status — 27 October 2026

## Executive status

**The local package is structurally audited and its included tests pass, but the full course Phase 2 gate is not complete.** The project is prepared for demonstration/review with outstanding instructor-supplied and independently verified evidence explicitly marked. Do not describe this as a fully passed submission or claim success on unavailable instructor inputs.

## Verified in this working copy

| Check | Latest result | Evidence |
|---|---:|---|
| Automated unit tests | 51/51 passed | `evidence/test_report.json` and `python -m unittest discover -v` |
| Expected CLI exit-code checks | 7/7 passed | `evidence/test_report.json` |
| Adapter comparison command | Runs; both conditions correctly reported blocked | `eval/adapter_comparison.csv` |
| Hard/error cases | 5/5 passed | `eval/error_results.json` |
| Local workflow cases | 8/8 passed, including injected transient tool fault | `eval/workflow_results.json` |
| Evaluation cases | 52 processed: 10 directory, 10 scheme, 10 statistics, 22 table/CSV | `eval/case_index.json`, `eval/results.json` |
| Macro-agent field F1 | 1.00 on the current source-derived benchmark | `eval/phase2_metrics.csv`; not evidence of independent document generalization |
| Held-out split field F1 | 1.00 (320/320 matched field tuples) | `eval/phase2_metrics.csv`; 10 Agmarknet cases, English CSV only, pending human verification |
| Structural audit | 12/12 checks passed | `evidence/audit_report.json` |
| Database dump/restore | Integrity and foreign-key checks pass; 607 observation rows in the current dump | `evidence/audit_report.json`, `db/dump/` |
| Training/evaluation exact-hash overlap | 0 exact-hash overlaps detected | `eval/contamination_report.json`; this does not test semantic overlap or pretrained-model contamination |

The automation log currently contains 428 persisted attempts. M12 is 336/428 = 0.785; M13 is 50/431 = 0.116. These are cumulative local-run measurements, including repeated evaluation and failure attempts, and should not be presented as a population-level automation estimate. Re-running evaluation changes these values.

## Source and agent mapping

`docs/source_agent_map.csv` maps all 23 inventory sources. The current mapping marks 3 as partial and 20 as pending. The project includes cards for implemented and planned roles under `docs/agents/`. Mapping a source to a planned agent does not mean that source has been implemented.

Implemented routes are narrow and rule-based:

- `directory`: KVK directory HTML.
- `scheme`: two-column Hindi scheme HTML; blank values remain explicit unknowns.
- `statistics`: structured observation CSV and a conservative production-sentence grammar for PDF text.
- `tables`: CSV/HTML/XLSX and selected PDF table/OCR cases.
- `supervisor`: fixed-rule routing, sequential specialist execution, hand-off on no data, bounded retries for transient tool faults, and terminal status reporting.

For PDFs, the supervisor can run statistics then tables. The pipeline does not use an LLM to make extraction or routing decisions by default. The optional Ollama header-mapping path has only been tested with a mock server; real model output was not verified in this environment.

### PDF/OCR run limits

To prevent pathological scans from hanging a demonstration, the table agent prioritizes agricultural-keyword pages, caps digital table extraction at 10 pages per run, caps scanned-page OCR at 2 pages and legacy-text re-OCR at 3 pages, renders OCR pages at 150 DPI, and applies a 5-second per-image Tesseract timeout. Remaining pages are outside the run's coverage. This is a responsiveness safeguard, not a claim of full-PDF coverage.

## Evaluation interpretation

`eval/phase2_metrics.csv` contains M1–M18 and separate agent/group/language scopes where applicable. The instructor's separate metrics CSV template was not included in the supplied files, so the current schema is explicitly provisional.

The 52-case benchmark is useful for regression and pipeline-mechanics evidence. The directory/scheme/statistics examples come from development-visible parent sources; the 22 table cases are source-derived Agmarknet CSV fragments, with 12 development and 10 held-out rows. A team member still needs to independently check the held-out references. A score of 1.00 on this benchmark does not establish generalization to unseen documents, arbitrary PDFs, scanned tables or instructor surprise inputs.

The current metric statuses are:

- **M1:** all 23 sources have a mapping (23/23).
- **M2:** 3/23 sources are partial; 20/23 remain pending.
- **M3–M10:** local measurements on the source-derived cases; M4 is a locator proxy and the other deterministic metrics have the documented limitations in `eval/README.md`.
- **M5:** awaiting three instructor surprise inputs and a checked answer key.
- **M11:** local workflow evaluation is 8/8, including transient tool-fault retry. LangSmith recording requires configured credentials/environment and must be shown live if required by the evaluator.
- **M12–M13:** computed from the cumulative automation log; repeated runs affect the denominator.
- **M14–M16:** local schema/validation/duplicate checks. M14 treats explicit `MISSING` tokens as populated fields, not known values; LGD codes remain unverified without an official registry.
- **M17:** awaiting three evaluator-selected database rows and live trace-back.
- **M18:** blocked. Training recipe and training examples exist, but no genuine trained adapter/base-model inference comparison has been run. Blank scores are intentional.

## Database and provenance

The schema, dictionary, SQLite database, SQL dump and JSON dump are included. Observation records carry source/source type, extracting agent, run ID, locator, crop, location, period, value and unit. The database round-trip and foreign-key checks pass. Some survey observations come from a manually transcribed PDF table and are marked as manual input; do not claim those rows were extracted automatically from the PDF.

## Remaining gates before claiming full Phase 2 completion

1. Obtain the instructor's actual metrics CSV template and map the provisional report into it.
2. Obtain and run the three surprise inputs; independently check 10–15 expected fields per input and fill M5 only from those results.
3. Have a teammate independently verify the 10 held-out Agmarknet references and document the checks.
4. Have the evaluator select three random database rows and demonstrate source-to-row traceability for M17.
5. Obtain the official district LGD registry if district codes are required; do not guess codes.
6. Run genuine base-model and trained-adapter inference on identical labelled cases with recorded model/adapter identity and hashes before reporting M18. No training or inference result is claimed now.
7. Confirm whether LangSmith traces, the separate metrics template, overdue submission handling, and a `phase2-submission` tag are required by the instructor. The uploaded ZIP has no Git history, and no commit, tag or push was created by this work.
8. Complete individual viva preparation and explain each team member's actual contribution without inventing commit history or attribution.

## Reproducible commands

From the project root:

```bash
python -m unittest discover -v
python eval/run_error_eval.py
python eval/run_eval.py
python eval/compare_adapters.py
python scripts/audit_project.py
python run.py --input data/raw/icar_kvk.html --trace
python run.py --input data/raw/msp_scheme.html --trace
python run.py --input data/raw/mp_economic_survey.pdf --trace
python scripts/db_cli.py --id 1
python scripts/db_cli.py --dump
```

The command `python scripts/run_verification.py` runs the functional test suite, representative success/partial/failure/fault paths, adapter blocked-state check, and database CLI checks. The extraction evaluation scripts are run separately so their outputs remain directly inspectable.
