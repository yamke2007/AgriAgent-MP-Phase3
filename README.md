# AgriAgent Madhya Pradesh

## Technical release

For the frozen technical submission, start with the [readiness report](docs/submission_readiness.md) and [file-by-file submission inventory](docs/submission_files.csv). The verified Windows setup uses Python 3.12. A clean checkout requires separately supplied corpus artifacts whose redistribution permissions are still under review. See [source rights](docs/technical_source_rights.md) before sharing files.

The release builder imports district crop production, extension directory, Hindi MSP scheme, and manually transcribed Economic Survey rows into a separate SQLite file. It leaves the historical database and evidence in place. Standard ingestion writes to `output/ingest`. Release data, demo data and benchmark data have separate output paths. See [technical progress and acceptance](docs/technical_progress.md), [live technical checks](docs/live_technical_checks.md) and [source rights](docs/technical_source_rights.md).

### Source-expansion and audit commands

```powershell
.venv-clean/Scripts/python.exe scripts/fetch_source_expansion.py --windows-trust
.venv-clean/Scripts/python.exe scripts/verify_source_expansion.py --output output/source-cohort-check
.venv-clean/Scripts/python.exe scripts/verify_source_expansion.py --direct-survey --output output/source-cohort-paired
.venv-clean/Scripts/python.exe scripts/compare_des_provenance.py --run output/source-cohort-check --output output/des-provenance-check.json
.venv-clean/Scripts/python.exe scripts/benchmark_real_ocr.py --source-run output/source-cohort-check --output output/real-ocr-check
.venv-clean/Scripts/python.exe scripts/verify_survey_automation.py --output output/survey-automation-check
.venv-clean/Scripts/python.exe scripts/verify_lgd_join.py data/source_expansion/lgd_mp_archive.csv --source-url https://ramseraph.github.io/opendata/lgd/data/districts.8edd1bf95e5bfeec.parquet --output output/lgd-join-check.json
```

The cohort checker requires the retained snapshots or exact source bytes matching the frozen hashes. See the cohort metadata for source permissions. The original M12 run was 10/17. The paired rerun kept the same 17 source cases and reached 11/17 by reading the original survey PDF directly for the same ten facts. Partial and failed inputs remain in both ledgers.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe -m unittest discover -v
.venv/Scripts/python.exe scripts/build_release.py
.venv/Scripts/python.exe scripts/query_release.py verify
.venv/Scripts/python.exe scripts/query_release.py q10
.venv/Scripts/python.exe scripts/analyze_release.py
```

For OCR install Tesseract and make its executable available on PATH. Point `TESSDATA_PREFIX` at the directory containing `eng.traineddata` and `hin.traineddata`, then verify with `tesseract --list-langs`. Enable tracing for a supervised demo with your own environment variables `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY`. Local JSON traces are written independently of LangSmith.

### Demonstration commands

```powershell
.venv/Scripts/python.exe run.py --config config.demo.json --input data/raw/icar_kvk.html --trace
.venv/Scripts/python.exe run.py --config config.demo.json --input data/raw/msp_scheme.html --trace
.venv/Scripts/python.exe run.py --config config.fault-demo.json --input tests/fixtures_tables/synthetic_district_apy.pdf --inject-tool-fault pdfplumber.extract_tables --trace
.venv/Scripts/python.exe scripts/query_release.py all
.venv/Scripts/python.exe scripts/db_cli.py --database output/release/agriagent.sqlite --id 1
.venv/Scripts/python.exe eval/run_surprise.py unseen-a.pdf unseen-b.xlsx unseen-c.html --output output/instructor-run
```

The CLI exits with 2 for a partial extraction. For M17 replace ID 1 with each ID selected by the TA. Q05 traces a district observation to its original CSV line and column. Q10 traces the state figures to the Economic Survey PDF page. Capture the surprise run first and pass `--score-existing --key <key.json> --output <capture-dir>` once the TA releases the key.

### Evaluation and model

```powershell
.venv/Scripts/python.exe scripts/fetch_eval_parents.py
.venv/Scripts/python.exe eval/run_eval.py --production-db output/release/agriagent.sqlite
.venv/Scripts/python.exe eval/run_error_eval.py
.venv/Scripts/python.exe scripts/prepare_review_queue.py
.venv/Scripts/python.exe scripts/package_colab.py
```

For the verified package, open `output/m18-verified/AgriAgent_M18.ipynb` in a fresh Colab session. Choose **Runtime → Change runtime type → T4 GPU**, then **Run all**. When prompted, upload the companion `output/m18-verified/agriagent-colab-inputs.zip`. It contains ten frozen inputs and training material. Held-out reference answers remain local. The notebook first installs the pinned libraries, then saves base predictions, trains QLoRA and runs adapter inference. At the end it downloads `agriagent-m18-results.zip`. Extract that ZIP into `output` so `output/m18/configuration.json` exists. Then score it locally.

```powershell
.venv/Scripts/python.exe eval/compare_adapters.py --run-dir output/m18
```

The retained Colab run measured **+0.6774 F1** on the ten frozen Agmarknet cases. [Verified M18 results](evidence/m18_release/verification.json)

For the actual tables agent, follow the [Windows CPU adapter instructions](docs/live_technical_checks.md#adapter-pipeline-on-windows-cpu). The adapter applies to the Agmarknet CSV layout and only accepts a prediction that resolves to a unique input cell. In the local check it confirmed four of sixteen fields. The deterministic control extracted all sixteen. The trace records whether the adapter ran and which fields it confirmed.

### Source and database maintenance

- Stage new files with `run.py --config config.demo.json --input <file> --source-url <url> --trace`. Check licenses and source values, then add the input metadata and SHA-256 to the manifest before adding the file to the explicit release corpus. Supply an official LGD registry to `scripts/build_release.py --lgd-registry <registry.json>` when available.
- Schedule the same staging command with Windows Task Scheduler using the absolute Python executable and project directory as the working directory. Run one writer per CSV automation log. The staging command records failed and partial runs for investigation.
- Use `scripts/db_cli.py --database output/release/agriagent.sqlite --dump --dump-dir output/ta-backup` and `scripts/restore_release.py output/ta-backup/agriagent.sql output/ta-restored.sqlite`. Use fresh output directories so prior execution evidence remains intact.
- The [production source metadata](data/production/sources.json) records the pinned download, original hash, geometry service and known terms. Retrieve the verified originals with `scripts/fetch_release_inputs.py`. With the original CSV, `scripts/prepare_query_references.py --output <new-file>` independently recomputes expected answers and `scripts/verify_release_formats.py` reproduces the workbook check. Local charts and maps are generated in `output/analysis`. The geometry layer has unverified redistribution terms.

## Historical Phase 2 review package

The material below describes earlier checkpoints. Current M18, source coverage, workflow metrics and acceptance status are in the technical progress and evaluator instructions linked above.

Runnable multi-agent extraction (LangGraph supervisor, four specialists including a general PDF/OCR/Excel table agent) with source evidence, normalization, validation, SQLite storage and reproducible local evaluation. **Phase 2 is partial; the live/model gates are not passed.** Four specialists are implemented: KVK directory HTML, Hindi scheme HTML, structured statistics CSV with a narrow production-sentence PDF grammar, and a general table agent (PDF tables, OCR English + Hindi, Excel, HTML, any CSV). The table agent has 22 source-derived Agmarknet CSV cases (12 development and 10 held-out); the held-out references still require independent teammate verification. The original 23-source Phase 1 inventory and TA work are preserved; the original README is in `docs/Phase1/README_original.md`.

## Quick start (Python 3.10+)

From this directory, install pinned packages and process an actual included source:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe run.py --input data/raw/icar_kvk.html
```

On Linux/macOS use `.venv/bin/python` instead. With dependencies installed in the current interpreter, the one-command entry point is:

```powershell
python run.py --input data/raw/icar_kvk.html
```

The directory snapshot produces 162 observations from 54 source rows. Every run prints a UUID/status/count and saves full records/evidence/trajectory in `output/<run_id>.json`, inserts observations into SQLite and appends one input-attempt row to `logs/automation_log.csv`. Repeated ingestion rejects natural-key duplicates and records rejection counts. Logs are sequential CSV, so use separate configs for concurrent processes. Existing acquisition/evaluation history is bundled as evidence; future runs append history.

## Supported workflow (supervisor + specialists, LangGraph)

```mermaid
flowchart TD
  A[run.py --input file(s) or folder] --> B[Size, type and content checks]
  B --> P[Supervisor plan: fixed rules]
  P --> D[directory: KVK HTML]
  P --> E[scheme: Hindi scheme HTML]
  P --> F[statistics: 6-column CSV / PDF sentences]
  P --> T[tables: PDF tables, OCR eng+hin, XLSX, HTML, any CSV]
  F -- PDF: no sentences = hand-off --> T
  D & E & F & T -- transient tool fault --> R[retry same agent, max 2]
  R --> P
  T -. unknown header .-> M[local LLM via Ollama, optional]
  D & E & F & T --> G[Normalize with declared rules]
  G --> H[Validate; attach hash, locator, evidence, agent]
  H --> I[Transactional SQLite with duplicate rejection]
  I --> J[JSON result, trajectory, agent trace, automation log]
  P -- unsupported / template / page limit --> K[Explicit failed result]
  K --> J
```

The supervisor (`agriagent/orchestrator.py`) plans one or more specialists per input with fixed rules, retries transient tool faults, records hand-offs between agents and decides when the plan is complete. For PDFs the statistics sentence grammar and the general table agent cooperate. The only model decision is optional: a local LLM (Ollama, no paid API) maps table headers the keyword rules cannot classify; if it is not running, those columns are skipped and noted, never guessed. No evaluation case ID or expected value drives extraction. See `docs/agents/supervisor.md` and `docs/agents/tables.md`.

Extra setup for OCR and the optional model (macOS): `brew install tesseract tesseract-lang` and, optionally, `brew install ollama && ollama serve & ollama pull qwen2.5:3b`. Optional tracing: `export LANGSMITH_TRACING=true LANGSMITH_API_KEY=<key>`.

New commands:

```powershell
python run.py --input C:/demo/ --trace                                   # every file in a folder, with agent/tool trace
python run.py --input data/raw/mp_economic_survey.pdf --trace            # statistics + tables hand-off
python run.py --input tests/fixtures_tables/synthetic_district_apy.pdf --inject-tool-fault pdfplumber.extract_tables --trace
python scripts/benchmark_hindi_ocr.py                                    # real Hindi text-layer vs OCR test
```

| Input | Operational scope | Limits |
|---|---|---|
| UTF-8 KVK HTML | Four columns: serial, address, host, sanction year; retains source row evidence | District extraction expects `Distt.`; source errors retained; current status/LGD unverified |
| UTF-8 Hindi scheme HTML | Two-cell label/value table with scheme/department context | Generic labels preserved in Hindi; no inference of crop/geography/effective date; blank values invalid |
| UTF-8 CSV | Headers `crop,location,period,variable,value,unit`; optional value_kind, origin_source, origin_locator, qualifier, lgd_code | Structured importer, not proof of DES portal retrieval |
| PDF | Explicit English production sentences plus bounded PDF-table/OCR hand-off | Partial coverage; at most 10 digital table pages, 2 scanned OCR pages and 3 legacy-text OCR pages per run; not arbitrary full-document extraction |

Useful real-source commands (partial returns exit code 2, failed returns 1):

```powershell
python run.py --input data/raw/msp_scheme.html
python run.py --input data/raw/mp_economic_survey.pdf
python run.py --input data/derived/survey_agriculture_transcription.csv
python run.py --input data/raw/evikas_calculator.html
python run.py --input data/raw/icar_kvk.html --fault extract
python scripts/db_cli.py --id 1
```

The scheme snapshot has 23 rows, some empty, so its run is partial. The survey PDF grammar extracts one wheat observation and explicitly warns of omitted facts. The ten-fact survey CSV was manually transcribed from page 7 and preserves lower bounds/targets; it must not be described as automatic PDF extraction. The e-Vikas template is deliberately rejected; fetching a template is not fetching fertilizer results. DES query HTML and the manual remain supporting/pending sources.

## Tests, evaluation and models

```powershell
python -m unittest discover -v
python eval/run_eval.py
python eval/compare_adapters.py
python scripts/benchmark_tools.py
python scripts/audit_project.py
```

See `evidence/test_report.json` and `evidence/clean_extraction_report.json` for executed commands/results, `evidence/tool_benchmarks.csv` for two actual PDF-tool runs, and `docs/phase2_implementation_status.md` for the final checklist. Initial repository contained no runnable tests; the current suite tests extraction, matching thresholds/units, faults, schema, duplicate detection, restore, corpus hashes, Phase 1 preservation and model-unavailable behavior.

`eval/cases/` and `eval/reference/` contain 30 source-verified fragments, ten per specialist, with a separate Hindi slice. They derive from three development-visible snapshots and include manually transcribed statistics; high local F1 is an importer/regression result, **not an independent held-out document or surprise gate result**. Source verification was performed by the implementing agent, not an independently labelled human panel. See `eval/README.md` for rules, denominators, contamination limitations and metric semantics before presenting results.

All M1–M18 IDs are represented, with unavailable values blank. M1–M4 and M6–M16 have local measurements (M8 via AgentEvals, M10 deterministic groundedness, M11 over eight workflow cases including a transient fault and retry); M4 is a local locator proxy. M5/M17 await the instructor and M18 stays blocked until genuine base and adapter predictions are produced; training examples and a Colab recipe exist (72 Agmarknet 2008–2010 examples, 0 exact-hash overlaps, no semantic/pretraining guarantee). The official separate metrics CSV attachment was not supplied: the current header is provisional, not certified as the exact required format.

The optional model runner and identical-case comparison workflow are documented in `eval/README.md`. No training or actual model/adapter inference occurred. Missing weights/dependencies produce blocked statuses; there are no fabricated scores. A separately collected training set, compatible base/PEFT weights, suitable compute and an independently checked evaluation set remain necessary.

## Configuration, provenance and troubleshooting

`config.json` controls database/output/log paths (relative to project root or absolute), byte/page limits and an optional authoritative LGD code/name JSON registry (build it from the official CSV with `scripts/import_lgd.py`). Use `--config <json>`, `--source-url <url>` and `--manual-interventions N` as needed; record runtime configuration changes during the demo as manual interventions. Paths do not depend on the current shell directory once the script is located.

Crop synonyms, unit conversions and period normalization are in `agriagent/normalization.py` and declared in `eval/README.md`. Unknown and inapplicable dimensions use explicit missing codes. Integer/code/decimal matching follows the protocol; incompatible units fail. No district code is inferred without a registry. Non-English labels are retained instead of silently translated. `data/manifest.csv` covers all raw/derived/evaluation corpus inputs with hashes, official URL, local collection date, language, lineage and explicit unverified licenses. Source snapshots are historical evidence, not current agricultural advice.

Database DDL, dictionary and portable dump are in `db/`. `scripts/db_cli.py` retrieves source hash/URL/input/locator for trace-back; historical absolute paths can be remapped using the manifest hash. `docs/agents/` contains operational and pending cards, and `docs/challenge.md` separates tool/literature capabilities from implemented behavior. The protocol PDF is preserved under `docs/evaluation_protocol.pdf`.

If imports fail, install `requirements.txt` with the same Python interpreter. If a portal snapshot is rejected, export actual results in the declared schema; do not replace placeholders with invented figures. A PDF with no supported sentence fails explicitly. An invalid row is retained with its validation errors; inspect output JSON. Database errors fail the run and retain output/log evidence; retry after correcting the config. Transient tool faults are retried up to the supervisor limit; deliberate extraction/database failures are logged and are not silently retried. Never bypass TLS verification to refresh source snapshots: the inventory ICAR hostname had an expired certificate, while official `icar.org.in` worked. `scripts/fetch_sources.py` preserves existing files by default and records genuine retrieval attempts.

For the timed session use `docs/demo_guide.md`. The protocol deadline predates this work and no submission tag, commit or push was created. For safe review/integration without overwriting unrelated work, use `docs/git_review_and_merge.md`. The exact requested archive filename is used for delivery despite the explicitly partial status; its name is not a claim that all evaluation gates passed.
