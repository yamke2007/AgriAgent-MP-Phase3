# Viva briefs (one page per member)

Each member should be able to open their files, run their command and answer the questions below in their own words. Numbers come from `eval/phase2_metrics.csv`, `eval/workflow_results.json` and `evidence/`. Say "measured locally" for every number: the TA re-runs the evaluation.

Common facts everyone should know:

* 52 evaluation cases (`eval/case_index.json`), 22 of them real Agmarknet table cases (12 development, 10 held-out).
* Pipeline: `run.py` → `agriagent/pipeline.py` → supervisor (`agriagent/orchestrator.py`, LangGraph) → specialist agents → normalization/validation → SQLite.
* Rule: a value is stored only if it is copied from the source. Missing values are explicit (`MISSING:not_in_source`); LGD codes are never guessed.
* Honest gaps: M2 source coverage is 3/23 (below the 0.2 floor); M18 needs the Colab run; no real PDF, scan or Hindi table case is checked yet.

---

## Aryan Mishra: Source and Data Engineering Lead

**Owns:** `docs/source_agent_map.csv`, `data/manifest.csv`, `scripts/fetch_sources.py`, `scripts/prepare_table_cases.py`, `agriagent/normalization.py`, `agriagent/storage.py`, `scripts/import_lgd.py`, `db/`.

**What to explain**

1. Source inventory: 23 sources, each mapped to an agent with a status (done/partial/pending) and a reason. Only 3 are partial, so M2 = 3/23. We did not mark a source done without a checked real file.
2. Manifest: every input has URL, collection date, language, licence note, sha256, parent file and transformation. The Agmarknet cases come from the public GitHub archive of official DMI data because the DES portal needs a login; the archive states no licence, which is flagged.
3. Normalization: NFKC text, crop synonyms (गेहूं → wheat, सोयाबीन → soybean), district aliases (Hoshangabad → narmadapuram), unit conversion with a fixed table; unknown units are rejected, not guessed.
4. Storage: SQLite with a UNIQUE natural key (source, crop, location, period, variable); duplicates are rejected and counted (M16). Dumps in `db/dump/` make the database reproducible.
5. LGD: `scripts/import_lgd.py` turns the official District LGD Codes CSV into `config/lgd_mp_districts.json`. A record gets a code only if its district name matches exactly one registry row; any other code fails validation.

**Code vs model:** all of this is deterministic code. No model touches storage or normalization.

**Likely questions**

* Why is M2 so low? Most portals are dynamic or need login; we report pending rather than claim coverage.
* How do you prevent duplicates? UNIQUE constraint plus the `attempts` table.
* What if a district is spelled wrongly in the source? It is kept as written (for example Ahoknagar); we add an alias only when it is certain.
* Show me the provenance of one stored value. Open `observations.payload` → `source`, `locator`, `evidence`.

Demo command: `python scripts/db_cli.py` (or `sqlite3 db/agriagent.sqlite "select crop,location,variable,value from observations limit 5"`).

---

## Unnati Goyal: Model Lead

**Owns:** `agriagent/orchestrator.py`, `agriagent/tables.py`, `agriagent/llm.py`, `agriagent/extractors.py`, `scripts/build_agmarknet_training.py`, `eval/train_lora_colab.py`, `eval/infer_adapter.py`, `docs/agents/`.

**What to explain**

1. Supervisor: `plan(path)` picks agents by file type (a PDF goes to statistics, then hands off to tables). A LangGraph StateGraph runs run_agent → retry (max 2) → next agent → finish. Every tool call is logged in a trace, which M8 and M11 score.
2. Tables agent tools: `pdf_tables` (pdfplumber), `ocr_tables` (Tesseract eng+hin word boxes rebuilt into rows), `read_xlsx`, `html_tables`, `read_csv_rows`. Headers are mapped to roles (crop, place, period, variable, unit) with English and Hindi word lists. Rows with a number but no crop and no place are dropped.
3. Crop from file name: Agmarknet files say the crop only in the name, so the caption context reads letters from the file name (`agmarknet_soyabean_2012` → soybean). This was the one bug found on development cases.
4. Hindi: the PDF text layer gave 0/35 correct Hindi words; Tesseract hin gave 26/35 (`evidence/hindi_ocr_benchmark.csv`). So the agent falls back to OCR when the text layer is broken.
5. LLM: optional Ollama model (qwen2.5:3b) is asked only to name the role of an unknown header. It never produces values. With the LLM off the pipeline still works.
6. LoRA (M18): 72 training examples from Agmarknet 2008-2010; evaluation uses 2011-2017; 0 hash overlap. QLoRA r=16 on Qwen2.5-1.5B-Instruct (Apache-2.0) on a Colab T4; base and adapter are scored on the same 52 cases by `eval/compare_adapters.py`.

**Code vs model:** values, units, dates and validation are code. The model may only choose a header role (live pipeline) or, in the M18 experiment, produce JSON that is scored against references.

**Likely questions**

* Why LangGraph? It gives an explicit graph with retry and hand-off states that we can trace and test (fault injection in `run.py --inject-tool-fault`).
* What happens if OCR misreads a number? Groundedness (M10) checks that the value string appears in the evidence; validation rejects out-of-range values. A misread that is still plausible is a known limit.
* Is the training data contaminated? Different years, exact-hash audit shows 0 overlap; semantic overlap cannot be ruled out by hashes.
* Why might the adapter not help? Training covers only CSV price rows; we report the signed delta either way.

Demo command: `python run.py tests/fixtures_tables/synthetic_district_apy.pdf --trace`.

---

## Yamke Sai Krishna Reddy: Evaluation Lead

**Owns:** `eval/run_eval.py`, `eval/scoring.py`, `eval/matching.py`, `eval/agent_metrics.py`, `eval/workflow_cases.json`, `eval/contamination.py`, `eval/compare_adapters.py`, `logs/automation_log.csv`, `tests/`.

**What to explain**

1. Matching rule: a field matches if crop, location, period and variable match after normalization, the units convert to the same base unit and the value is within ±1% after conversion (integers, codes and text must be exact). F1 is macro-averaged across agents so one large agent cannot hide another.
2. References are written by scripts from the raw source lines, not by the pipeline; every case has a `checked` field that a team member must confirm. Held-out tables cases were generated after development and scored once.
3. M8: AgentEvals `create_trajectory_match_evaluator` (strict, exact tool args) compares the agent's tool calls with the expected trajectory.
4. M10 groundedness: deterministic; the exact value string must be in the evidence the tool returned for that locator. No LLM judge, so no judge calibration is needed.
5. M11 workflow: 8 runs in `eval/workflow_cases.json`, including an injected tool fault that must be retried; 8/8 completed.
6. Automation log: every run writes agents, hand-offs, retries, LLM calls and manual interventions, which feed M12 and M13.
7. Contamination: sha256 of every training file against every case and parent source; result 0 overlaps.

**Code vs model:** the whole evaluation is deterministic code; no model grades anything.

**Likely questions**

* Why do most metrics show 1.0? Cases are small and many are CSV imports; the held-out cases are English CSV only. We say this in the notes column and do not claim it generalises to scans.
* How would you catch a hard-coded answer? `test_unseen_value_not_hardcoded` plus held-out cases from unseen years.
* What is M4 here? A local locator proxy; the TA must still check source values.
* Which metrics are not yours to measure? M5 and M17 are instructor-scored; M18 waits for the Colab run.

Demo command: `python eval/run_eval.py` then `python -m unittest discover -s tests`.

---

## What nobody should claim

* That any source is fully covered, or that real PDF, scan or Hindi table extraction is validated.
* That the LoRA adapter improves results before the Colab run is done.
* That LGD codes are attached in the submitted database (the official CSV still has to be imported).
* That this code was written on the dates of the git history; describe your own commits only.
