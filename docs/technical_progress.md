# Technical progress and acceptance

## Final laptop verification

- The DES PDF generated 52 records in 4.66 seconds and stored 52 observations. All five sampled citations matched the original PDF cells. The separate 7.73-second fault run recovered with one retry and zero final errors.
- The official ministry workbook, its CSV conversion and the 55-district registry match. The read-only verification matched all 52 historical release districts, all 1,886 panel rows and all 52 geometry districts.
- The pinned base and trained adapter hashes matched. The laptop application generated successfully and returned four confirmed fields out of sixteen in 276.78 seconds, with zero unmatched predictions and a partial status.
- The laptop backup restored 3,980 observations. The final check passed 62 of 62 tests and ten of ten queries on both the original release and laptop-restored database. Remote LangSmith visualization is owner-reported, with the local hand-off and retry independently verified.

See the [readiness report](submission_readiness.md) and [laptop artifact verification](../evidence/final_submission/laptop-verification.json).

## Latest protocol recheck

- The paired source-cohort rerun measured **11/17 unattended (64.7%)**, up from **10/17 (58.8%)**. The original PDF supplies the same ten survey facts without a manual transcription. Four partial and two failed inputs remain in the denominator. The 80% target requires 14 of 17 unattended completions.
- The 52-case local evaluation resolved **402/402 original-source locators**, including the ten survey records verified directly against PDF page 7. Per-agent scores and their equal-weight macro means were independently recalculated. M11 now includes the partial run in its local planned multi-agent denominator and measured **1/2**. The real DES report recovered from a separately injected fault in one retry and produced 52 records.
- The original release database, historical database, nine visualization PNGs, GIF, source map and M18 files matched all 33 before/after hashes. The GIF contains seven frames.
- The actual tables agent loaded the SHA-256-verified pinned Qwen base and trained adapter and recorded a successful `llm.peft_extraction` call. The CPU run confirmed four of sixteen fields on `tables_14`, so the application reported a partial result. The deterministic control matched all sixteen. This separate integration check leaves the Colab M18 score in place.
- A fresh Python 3.12 Windows virtual environment installed `requirements.txt`, passed `pip check` and ran **62/62 tests** with English and Hindi OCR. All ten queries matched against the existing, rebuilt and restored 3,980-observation databases. A separate 321-file working copy built and queried the release without prior output files.

See the [requirement-by-requirement audit](technical_acceptance_audit.md), [metrics snapshot](../evidence/technical_completion/phase2_metrics.csv), [live commands](live_technical_checks.md), and [licensing review](technical_source_rights.md).

## Verified Colab M18 run

- The Tesla T4 export records three epochs, 27 optimizer steps, 4-bit NF4 quantization, and LoRA rank 16 on the pinned Qwen2.5-1.5B-Instruct revision. All 17 manifest hashes matched and all 18 ZIP files matched their extracted copies. The adapter contained 224 finite tensors and all 112 LoRA B tensors had nonzero values. Trainer-reported time was 267.1 seconds within the longer Colab workflow.
- The run matches the frozen 72-example training set and the ten held-out English Agmarknet CSV cases. Training parents are from 2008–2010 and held-out parents are from 2011, 2013, and 2017. The file and parent-lineage checks found zero overlap. The Colab input ZIP excluded the held-out references. Independent reference review and base-model pretraining overlap are unresolved.
- The base scored precision, recall, and F1 of **0.0000** (0 TP, 56 FP, 160 FN). The adapter scored **0.9545 precision, 0.5250 recall, and 0.6774 F1** (84 TP, 4 FP, 76 FN). **M18 is +0.677419 F1.** The base had one JSON decode failure; the adapter had zero. The published scoring rules and prediction files were used as exported.

The [M18 evaluation snapshot](../evidence/m18_release/phase2_metrics.csv) updates M18 from the prior local metrics snapshot. Earlier evaluation files and the separate source-expansion measurements remain available. See the [verification report](../evidence/m18_release/verification.json) and [per-case results](../evidence/m18_release/case_scores.csv). The actual adapter is under `output/m18/adapter`.

The post-Colab recheck passed [61 of 61 regression tests](../evidence/m18_release/unittest.txt) and [10 of 10 Phase 3 queries](../evidence/m18_release/query_recheck.json) against the original release database in read-only mode.

## Source and automation follow-up

- **M2 reached 14/23 (60.9%).** Added eight source-scoped implementations after formal extraction and validation on the declared inputs. See [source map](source_agent_map.csv) and [frozen cohort](../data/source_expansion/cohort.json) for exact URLs, hashes, scopes, and license statuses. The overall source gate still requires instructor review.
- **M12 measured 10/17 (58.8%)** in the expanded genuine-input cohort. Eleven inputs completed, four were partial, and two failed. The complete scripted CSV ingestion that depended on a historical manual transcription carries one manual intervention. The original four remain 2/4 when measured from acquisition-ready inputs and 1/4 when that upstream transcription is included. The original Hindi MSP sheet has five blank fields. Direct DES exports confirm all thirteen missing summer production cells in the release CSV. Neither input was promoted to complete or filled with inferred values.
- A **separate unattended survey PDF pilot** matched all ten data points in the retained transcription with one tool call and zero interventions. This demonstrates that the scoped report can be ingested directly. The original and expanded M12 cohorts remain fixed.
- **Agricultural provenance** now has direct DES corroboration of 104/104 district area and production cells for 2022–23 Rabi wheat. Its separate major-district PDF agrees on 52/52 production rows. This scope does not establish identity for the full bulk mirror.
- **LGD join** matched all 52 release districts, 1,886 release rows and 52 historical geometry names to the hash-verified archived LGD snapshot observed 23 November 2026. The current archived register has 55 MP districts. Maihar, Mauganj and Pandhurna are outside the historical boundary layer. The live Ministry download was not retrieved; the audit used the archived official-origin table and ran against the existing database read-only.
- **Real OCR** matched 15/15 dated values in the image-only Sehore bulletin. A low-resolution OCR run misread one temperature and was retained. The revised numeric pass uses 220 DPI. The Hindi legacy-font PDF benchmark measured 3.45% character error and 13.04% word error on three image regions. OCR matched 1/3 regions exactly and the native text layer matched 0/3. The real DES ranking also recovered an injected extraction fault with one retry and returned all 52 records. These are local checks with small source samples.
- **Licensing** was checked per publisher. The MP Agricultural Engineering copyright page specifies reproduction permission for listed material. The e-NAM snapshots carry copyright notices. The public DES exports, IMD bulletin, other publisher documents and historical geometry remain scoped for local academic verification pending reuse confirmation. The government OGD catalog license is not inferred for other portals or the agricultural mirror.
- **M18 preflight** verified the updated 90-member input package, all 72 source-linked training examples with 1,152 target cells, and ten frozen held-out cases. The pinned tokenizer measured 1,381 tokens for the longest training sequence and 1,024 for the longest target, within their 4,096 and 1,280 limits. A tiny randomly initialized CPU model exercised TRL training, adapter save/reload through the application loader, and inference before the genuine GPU run.

Follow-up evidence is retained under `evidence/source_expansion`. The original technical release remains the basis for the ten-query and visualization artifacts. The follow-up cohort, OCR, and GPU-preflight artifacts use separate paths.

Follow-up verification passed 10 targeted tests and all 61 regression tests with English and Hindi Tesseract packs. The ten-query suite passed again against the original release database in read-only mode.

## Preserved baseline

The local archive `AgriAgent-pre-implementation.zip` contains the tracked baseline at commit `7f28d64f7b812d8db36272e41f97199ec1e9f60a`. The official requirements and historical SQLite, logs, dumps and result exports remain in place. The recorded original byte sequences of 40 files were recovered and verified against their existing SHA-256 values. The default CLI, release, demo, fault demo, evaluation and robustness runs each have separate output directories.

## Phase 2

- [x] Map all 23 inventory entries. The source expansion increased verified partial implementation from six to fourteen.
- [x] Verify genuine CSV, Hindi HTML and PDF extraction, and a workbook made from ten genuine source cells. Verify English/Hindi scan parsing with synthetic fixtures.
- [x] Execute the local 52-case extraction evaluation. Verify 19/19 original Agmarknet parent files by hash. Compute per-agent metrics, equal-agent macro averages, errors, sample counts and run latency. M4 checks 392 of 402 records at original source locations. The other ten were manually transcribed from the Economic Survey and need an independent check.
- [x] Exercise the LangGraph hand-off and retry. The synthetic PDF retry reuses the successful page inspection and reruns the failed table extraction once. The real-input runs cover documented failure and partial paths.
- [x] Verify production schema, a clean release database, automation evidence and SQL restore. M12 and M13 on the positive cohort were 52/52 and 0/52 respectively. Only two of four genuine release inputs completed because the other two had missing source cells. This evaluation does not establish production performance at the official targets.
- [ ] Independently check the case labels and trajectories. Use `output/reviewer_queue.csv` and start with the ten frozen held-out cases. The queue records no approvals.
- [ ] Apply the TA's metrics template and run the three instructor inputs for M5. Collect the live LangSmith trace and fault recovery for M11 and perform the evaluator-selected rows for M17.
- [x] Verify the genuine CUDA QLoRA run and score both exported prediction sets on identical held-out cases. Verify the same trained adapter loads and generates through the optional local pipeline and report the observed partial extraction.

## Phase 3

- [x] Build and restore the isolated 3,980-observation SQLite release. Its district input has 1,899 original source rows, including 13 missing production cells and 1,886 complete area/production pairs. The input is a pinned mirror of DES-origin data. Byte identity with the government portal export is unverified.
- [x] Verify ten ordered query results against the raw-source answers, including three spatial, two temporal and two provenance queries. Q10 verifies the local transcription; the TA can open the cited PDF page.
- [x] Generate and record three quantified relationships, two statistical charts, seven district maps and a seven-frame GIF. The maps use 52 Survey of India district features published through Esri India. The geometry's redistribution terms and its use at any eventual submission remain to be confirmed.
- [x] Verify setup and release rebuild with an isolated Windows environment. `pip check` passed and 56 of 56 regression tests passed with English and Hindi OCR enabled. Document source addition, adapter activation, isolated scheduling commands and database backup/restore.
- [x] Verify district-code joins against the archived snapshot and direct ministry workbook using documented normalized names. Retain the direct export, converted CSV and generated registry as local evidence.
- [ ] Run all ten queries live with the TA. Confirm actual team attribution, the Phase 2 gate, and release tag logistics before submission. No push or publication was performed.

Exact technical commands are in the README. Local release artifacts are under `output/release`, `output/evaluation-release`, `output/robustness-release`, `output/analysis`, `output/formats`, and `output/colab-release`.
