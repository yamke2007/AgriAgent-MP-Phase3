# Evaluation contract

The current evaluator writes only to a new output directory. Run `python scripts/fetch_eval_parents.py` to retrieve and hash-check the annual Agmarknet originals, then `python eval/run_eval.py --production-db output/release/agriagent.sqlite --output output/evaluation-recheck`. M10 resolves the specified row and column and checks the whole normalized tuple. M4 checks original HTML rows, archived Agmarknet rows and the original Economic Survey PDF page for the ten statistics cases. Use `scripts/verify_release_formats.py` for separate PDF and spreadsheet verification.

The [current metrics snapshot](../evidence/technical_completion/phase2_metrics.csv) combines the local benchmark rerun, both genuine-input M12 ledgers and the verified M18 result. Its CSV format remains provisional pending the TA attachment. See [protocol and scope details](../docs/technical_acceptance_audit.md).

For M18 use `python scripts/package_colab.py` and the generated notebook. The package contains only the ten frozen held-out inputs and source-linked training examples. Their references stay local. The annual original-source hashes and parent paths are checked for separation. The independent human review remains pending. Compare the exported predictions with `python eval/compare_adapters.py --run-dir output/m18`.

The verified Colab run scored **0.0000 base F1** and **0.6774 adapter F1** on the ten frozen cases. [Comparison CSV](../evidence/m18_release/adapter_comparison.csv) · [Precision, recall, and artifact checks](../evidence/m18_release/verification.json) · [Versioned M18 metrics](../evidence/m18_release/phase2_metrics.csv)

## Historical Phase 2 run notes

Run `python eval/run_eval.py` from the project root. It processes all 30 source-derived fragments, writes real automation entries, evaluates field tuples, refreshes the SQLite dump, and writes per-case evidence. Repeated runs append genuine attempts; M12 consequently describes accumulated runs at report time. Test isolation uses temporary logs and databases.

## Set and verification

`case_index.json` lists ten directory, ten scheme (Hindi), and ten statistics cases. Inputs and references are separate. `scripts/prepare_cases.py` documents their construction without calling production extractors to produce labels. The directory address/host labels use an independent cell transcription; district/year pairs and ten Hindi policy labels/values were checked by the implementing agent against source text. Statistical references were checked against rendered PDF page 7. No human verification is claimed. Source locators, parent hashes and input hashes are recorded with each reference.

These are 30 record/fragment cases drawn from **three source snapshots**, not 30 independent unseen documents. The source documents and references were visible during development. Statistics CSV fragments are manual transcriptions and measure the CSV importer; they do not measure automatic PDF extraction. The implemented PDF grammar has a separate real-source functional test, extracting one wheat observation. This benchmark demonstrates mechanics and regressions, and does not establish the full Phase 2 held-out generalization gate. Obtain independent, human-checked documents before claiming that gate. Five source-backed hard/error checks are defined in `error_cases/index.json`: run `python eval/run_error_eval.py`. They report expected failure/partial outcomes separately rather than inflating extraction F1 with fabricated positive facts. Further adversarial cases are in `tests/test_project.py`.

`data/train/` holds 72 training examples built by `scripts/build_agmarknet_training.py` from real Agmarknet records for 2008-2010 (soybean, wheat, maize; Madhya Pradesh markets). Evaluation cases use 2011-2017 only. Targets are copied from the source cells by the script (no model); spot-check 5 before training. `contamination_report.json` checks SHA-256 equality for training files against cases and parent raw sources: 73 training files, 0 overlaps. Hashes do not establish pretraining or semantic independence. Do not train on the benchmark, raw parent sources or their transformations.

## M18 on Colab

1. `zip -r colab_upload.zip data/train/examples.jsonl eval/case_index.json eval/cases eval/train_lora_colab.py`
2. In a Colab T4 notebook: upload, `!unzip colab_upload.zip`, `!pip install -q "transformers>=4.45" "peft>=0.13" "trl>=0.11" datasets accelerate bitsandbytes`, `!python eval/train_lora_colab.py`
3. Download `output/base.json`, `output/adapter.json` and `adapter/`, then run `python eval/compare_adapters.py --base output/base.json --adapter output/adapter.json --model-id Qwen/Qwen2.5-1.5B-Instruct --adapter-id agriagent-lora-r16`.

The training set covers only Agmarknet-style CSV price rows, so the adapter is expected to help the tables cases most; a negative or zero delta on other agents is a valid result if reported.

## Matching and normalization

NFKC Unicode normalization and whitespace collapse apply to textual values. Crop synonyms: गेहूं/गेहूँ→wheat, धान/paddy→rice, चना/gram→chickpea, सोयाबीन→soybean, मक्का→maize, कपास→cotton. English crop/location names are case-folded; MP/मध्य प्रदेश→madhya pradesh. Other district spellings remain as written, including source errors such as Ahoknagar. No speculative correction or fabricated LGD code. Supply an independently verified code→name JSON registry through `lgd_registry` (build it with `python scripts/import_lgd.py <official District LGD Codes CSV>`); when set, a record gets `lgd_code` only if its district name matches exactly one registry entry; supplied but unverifiable codes fail validation.

Dates DD-MM-YYYY or DD/MM/YYYY become ISO dates; years and financial years remain explicit. `MISSING:not_in_source` and `MISSING:not_applicable` are distinct, retained case-sensitively. The protocol does not specify a literal missing token, so these are a project convention. A missing value fails validation; missing dimensions encoded explicitly count for M14 and are not invented facts.

Each observation is one field tuple: crop, location, period, variable, value and unit. Context and variable must match; integer values are numerically exact, codes textually exact; decimals allow **±1% relative** after conversion. Zero requires exact zero. Unit conversions are declared in `agriagent/normalization.py`: kg/quintal/lakh tonnes→tonnes; lakh hectare→hectare; lakh farmers→count; percentages remain percentages. Incompatible units fail. Text values and units match exactly after whitespace/Unicode normalization. Distinct quantities such as lower bounds and targets have distinct variable names and retain qualifiers.

One-to-one matching prevents duplicate predictions from earning repeated credit. TP is matched tuples, FP unmatched outputs, FN unmatched references, F1=2TP/(2TP+FP+FN). Missing/wrong context/value/unit yields both an FP and FN. No reference field is excluded for missing context. Report per agent, Document/Database group, English/Hindi, pooled end_to_end and **equal-agent macro average**. Both sources in Document are English/Hindi; `language:hi` is a language slice, not an additional PDF-defined source group.

## Metrics and evidence limits

The PDF's p8 says a separate CSV is attached. The actual PDF has no attachments and no header printed. `phase2_metrics.csv` therefore uses the **provisional** columns `metric_id,scope,value,numerator,denominator,floor,target,direction,status,evidence,notes`. Exact instructor-template compliance is blocked until supplied; do not silently certify this layout.

M1/M2 use all 23 original inventory rows (not the expanded cleaned mapping); sources 6/21/23 are partial, the other 20 pending. M3 and M6–M9 are local benchmark measurements. M4 resolves local table/CSV locators and checks value presence; it is explicitly a proxy pending evaluator semantic inspection. M6 checks extractor identity, M7 exact input hash/schema/page arguments. M8 now uses AgentEvals (`create_trajectory_match_evaluator`, mode `strict`, tool arguments `exact`) on the recorded trajectory converted to tool-call messages (`eval/agent_metrics.py`). Routing, normalization and SQL are fixed code, not LLM tools. M9 requires complete status and every row schema-valid, allowing explicit missing context codes; missing value rows fail.

M5 awaits instructor inputs/answer key. M10 is now measured deterministically: a value is grounded when its exact string appears in the source evidence (row text) returned by the tool at that locator; no LLM judge is used, so judge calibration does not apply; explicit MISSING values count as not grounded. M11 is measured over `eval/workflow_cases.json` (real and clearly marked synthetic inputs): a run is correct when it reaches the expected terminal status with the expected agent plan; one case injects a transient tool fault that must be recovered by a retry. Results: `eval/workflow_results.json`. LangSmith tracing is optional (`LANGSMITH_TRACING=true`). Fault containment is tested independently. M12 is complete/no-manual inputs divided by every persisted attempt, including partial/failed runs. Manual preparation of transcription data is disclosed and not represented as automatic extraction; supply `--manual-interventions N` for manual runtime adjustments. M13 uses actual extractor calls minus declared reference calls divided by actual calls; no retries are implemented, so retry count is zero. Unsupported routing attempts have zero calls/reference calls.

M14 SQL checks nonempty mandatory columns including explicit missing codes. M15 tests the declared type/unit/date/range rules (ordinary numbers 0–1e14; percentage shares 0–100; percentage variables ending `_growth` may exceed 100 and have a lower bound of -100), not general agronomic correctness. A supplied LGD code requires a verified registry; most location names have no codes, so official LGD accuracy is **unverified**. M16 counts all rows in duplicate natural-key groups divided by stored rows; UNIQUE rejects duplicate insertions and `attempts` records rejection counts. M17 awaits three evaluator-selected traces. M18 remains blocked until genuine base/adapter predictions exist on the identical case set and training-overlap evidence is established.

Floors and targets for M1–M17 are copied from protocol pp5–6, including lower-is-better M13 (.50→.10) and M16 (.10→0). `scoring.py` implements clipped linear interpolation for either direction; no project grade is asserted. M18 has no numeric floor/target in the PDF.

## Adapter workflow

`python eval/compare_adapters.py` emits explicit blocked rows with blank scores. It is a tested scorer, not model execution. For locally available compatible causal model and PEFT weights, optionally install `torch transformers peft` in a separate environment, then run:

```powershell
python eval/infer_adapter.py --model C:/models/base --output output/base.json
python eval/infer_adapter.py --model C:/models/base --adapter C:/models/lora --output output/adapter.json
python eval/compare_adapters.py --base output/base.json --adapter output/adapter.json --model-id publisher/model@revision --adapter-id local-adapter@revision
```

The runner reads only inputs (never gold values), runs greedy CPU inference, records generation configuration and failures, and never downloads weights or executes remote model code. Its missing-dependency/model branch is tested; actual generation is **implemented but untested** here. Generated failures are empty predictions and count as FN. Compare F1 is macro-average across agents, M18=F1(adapter)−F1(base); counts are pooled for additional transparency. Both conditions must have all case IDs, identical case/input/reference digest, explicit model/adapter identity, and prediction hashes. Producer execution cannot be attested from a prediction JSON alone. The training recipe is `eval/train_lora_colab.py` with the separately collected set in `data/train/`; no trained adapter or M18 score is claimed until that run is done.


## Tables agent cases (added 25 Oct)

`eval/cases/tables_01..22_*.csv` are real Agmarknet daily price records for Madhya Pradesh markets (soybean, wheat, maize; 2011-2017), each 4 unmodified source lines plus Agmarknet's column header. Parent files are identified by URL and sha256 (`parent_remote: true`); they are not stored in the repo (4-11 MB each). References come from `scripts/prepare_table_cases.py`, which reads the raw cells directly and never calls the pipeline. `split` is `development` for tables_01-12 (used while building, one bug fixed) and `heldout` for tables_13-22 (generated afterwards, scored once); run_eval reports both splits separately (`split:development`, `split:heldout`). `checked` reads `drafted_from_source_lines_by_script_needs_team_check` until a team member verifies each case against the source lines stored in the reference evidence.
