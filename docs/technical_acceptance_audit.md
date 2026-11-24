# Phase 2 and Phase 3 technical acceptance

This audit uses the Phase 2 detailed protocol, Phase III evaluation grid and project methodology in `Official_Requirements`. Status refers to local technical evidence. Instructor gates and assessed work require the named evaluator.

The [submission readiness report](submission_readiness.md) and [laptop artifact verification](../evidence/final_submission/laptop-verification.json) add the final DES, adapter, restore and direct ministry LGD results. All previous metric snapshots remain available.

## Phase 2 metrics

The [current measurement snapshot](../evidence/technical_completion/phase2_metrics.csv) has a provisional header. The PDF refers to a separate CSV attachment, which is absent. The snapshot retains source-group, agent, language, pooled and equal-agent views so the measured rows can be exported to the TA's template when supplied. The 52 cases comprise 10 directory, 10 scheme, 10 statistics and 22 tables cases. Document contains 20 and Database 32. Positive local results use source fragments and controlled imports with shared or development-visible parents. Independent reference and trajectory checks are pending.

| Metric | Rechecked local result | Official requirement still open |
| --- | --- | --- |
| M1 Source mapping | 23/23 | Live spot checks |
| M2 Implementation coverage | 14/23, 60.87%, counting declared partial scopes | Live spot checks and any required scope sign-off |
| M3 Field F1 | 1.000 equal-agent macro across four agents; pooled 402 TP, 0 FP, 0 FN | Check references against original sources independently; local benchmark has constrained scope |
| M4 Provenance | 1.000 equal-agent macro; 402/402 original locators resolved locally, including ten survey PDF facts and 392 HTML/CSV-backed records | Evaluator opens sampled sources |
| M5 Surprise F1 | Pending; capture rehearsed with known inputs and saved-run scoring exercised in a unit test | Three instructor inputs, including one Hindi item, and the checked answer key |
| M6 Tool selection | 1.000 equal-agent macro; 52/52 expected tools | Review reference trajectories; positive cohort mostly one-step routes |
| M7 Tool inputs | 1.000 equal-agent macro; 52/52 correct tool-and-argument matches | Reference review and live behavior |
| M8 Trajectory | 1.000 equal-agent macro; 52/52 strict exact-argument matches in AgentEvals | Independent trajectory review |
| M9 Completion | 1.000 equal-agent macro; 52/52 schema-valid complete cases | Scope limited to the declared benchmark |
| M10 Groundedness | 1.000 equal-agent macro; 402/402 supported field tuples in input cells | Deterministic evaluator. LLM judge calibration applies only if such a judge is used |
| M11 Workflow and fault | 1/2 correct complete in the planned local mixed cohort. The laptop DES run recovered with one retry, returned 52 observations and took 7.73 seconds | The owner reports viewing the remote trace. Retain a workspace-approved trace link or export for evaluator confirmation |
| M12 Automation | Original frozen 10/17, 58.82%; matched 17-case direct-PDF follow-up 11/17, 64.71% | 14/17 reaches the 80% target. Three more unattended completions needed |
| M13 Redundant calls | 0/52 in benchmark, zero retries; actual calls include LLM calls where present | Production-wide reference counts are incomplete. Keep retries separate and never infer blank reference counts |
| M14 Mandatory fields | 3,980/3,980, including explicitly coded missing dimensions | Confirm semantics with evaluator |
| M15 Validation | 3,975/3,980, 99.87%, under release validation rules. The official workbook independently matches all 52 historical district names and all 1,886 panel rows | Evaluator rule verification. The direct join was read-only and did not alter the frozen database or retroactively recompute M15 |
| M16 Duplicate rate | 0/3,980 rows sharing the declared key | Review stored enforcement and rejected insertion attempts |
| M17 Live trace-back | Local read-only command exercised; no M17 score | TA selects three observation IDs and checks each against the original |
| M18 Adapter comparison | Baseline F1 0.0000, adapter 0.677419, delta +0.677419 on ten frozen cases | Independent reference review and evaluator confirmation |

For M3–M4 and M6–M10, per-agent estimates use the metric's counts for that agent, then take the arithmetic mean of four agent estimates. Pooled totals and source-group results are diagnostic. The matching rules normalize crop, location, time and units, require exact integers and codes, and allow ±1% relative error for decimals. The [independent aggregation calculation](../evidence/technical_completion/agent_aggregation_check.json) rechecked all four agent rows from case counts. Case evidence includes latency, errors, retries and LLM calls. The deterministic benchmark has zero LLM calls. Optional token usage is logged in model traces.

The [CPU adapter application check](../evidence/technical_completion/adapter_pipeline_check.json) verified both model hashes, a successful PEFT tool call and four source-confirmed fields on `tables_14`. Twelve reference fields were missed and no false positives were emitted. The deterministic control extracted all sixteen. The 504-second CPU check used an unquantized base. The separately measured Colab M18 uses its original ten-case GPU export.

Other protocol items are available locally in the source-to-agent map, agent cards, challenge/tool tests, orchestration and one-command entry point, schema/dictionary/dump, evaluation scripts, manifest and M18 artifact. Present real English and Hindi OCR evidence with scope. The retained tests covered 15/15 English dated fields and three Hindi regions with 3.45% CER and 13.04% WER. Individual attribution, viva and the Phase 2 gate remain evaluator-dependent.

### M12 case investigation

| Original case | Paired rerun | Finding and required input |
| --- | --- | --- |
| S23 Economic Survey transcription | Complete, 0 interventions, 10 TP / 0 FP / 0 FN | The original PDF directly supplies the ten pre-existing facts using the scoped survey parser. The historical manual run remains in the original ledger. |
| S06 Hindi MSP scheme | Partial, 18/23 valid fields | A fresh publisher response matched retained bytes exactly. Start date, designated officer, time limit, benefit amount and attached documents are blank. Ask the publisher for an authoritative completed record. |
| S11 bulk crop CSV | Partial, 3,785 extracted fields | Direct DES documents agree that thirteen summer production cells are blank. An updated authoritative export covering the same observations is needed to resolve the missing fields. |
| S11 summer rice report | Partial, 44 extracted fields | The same-season direct report has blank production cells. Ask DES for completed rows or a documented corrected export. |
| S11 summer maize report | Partial, 83 extracted fields | The same-season direct report has blank production cells. Ask DES for completed rows or a documented corrected export. |
| S03 mandi rates | Failed, zero observations | Public HTML is a form with a CAPTCHA. A user can select the report parameters, complete CAPTCHA and save real results for inspection, or obtain an approved unattended feed. Manual acquisition remains an intervention. |
| S19 e-NAM online trading | Failed, zero observations | Public HTML contains the empty results table. The public endpoint used by that page returned HTTP 200 HTML, with no usable JSON state rows. Open the current publisher page, wait for the live table and save a dated export if rows render. Request a supported feed or publisher help if unavailable. Record manually acquired exports as interventions. |

The [paired report](../evidence/technical_completion/m12_paired.json) checks every slot, and the [automation log](../evidence/technical_completion/m12_paired_automation.csv) records every attempt. See [publisher access](../evidence/technical_completion/source_access.json) and [DES provenance](../evidence/source_expansion/des_provenance.json). The 52-case benchmark's 52/52 completion rate describes test inputs only.

## Phase 3 evaluation grid

| Criterion | Technical status |
| --- | --- |
| R1 Research and positioning | Problem/state and related-tool evidence available. The report and its research synthesis are deferred. |
| R2 Methodology | Local sources, four agents, orchestration, pinned model/adapter, schema and model-versus-code decisions are implemented. Report tables are deferred. |
| R3 Rigour | Local metrics include sample sizes, per-agent and macro results, error counts, frozen base/adapter comparison and ten expected queries. Independent and live evaluations remain pending. |
| R4 Limitations, ethics and licensing | Technical limitations, provenance and license restrictions are recorded. Exact rights for some pinned sources and derivative files remain open. |
| R5 Report formatting | Deferred. |
| P1–P3 Poster content, results and design | Underlying results, counts and figures are retained. Poster and layout are deferred. |
| P4 Spatial infographics | Two charts, seven district maps and seven animation frames exist. Maps use named historical SoI features. Rights for the exact layer and TA approval remain open. |
| T1 Presentation structure | Deferred. |
| T2 Technical depth | Architecture, control flow, trace, schema and adapter evidence are available. Oral assessment is pending. |
| T3 Live queries | 10/10 pass locally, including three spatial, two temporal and two provenance queries. Q10 links to the original survey PDF page. Run all ten live with the evaluator. |
| T4 Visualizations and animations | Seven annual district maps and one seven-frame GIF retained, alongside two plots and three quantified relationships. Oral/visual handling remains for the session. |
| U1 Fresh-machine setup | A fresh Python 3.12 Windows virtual environment installed the requirements and passed dependency checks and 62/62 tests. TA must run the quick start independently on the evaluation machine and score unassisted steps. |
| U2 Usage and maintenance | Runnable extraction, traces, querying, external configuration, source additions, adapter activation, scheduling commands, backup/restore and logs. Formal manual is deferred. |
| U3 Troubleshooting and FAQs | Real failure evidence and README troubleshooting are available. The formal eight-problem and ten-FAQ requirements remain deferred with the manual. |
| U4 Walkthrough | Deferred. |
| G1 Reproducibility | A separate 321-file working copy ran extraction, release build and validation with no prior outputs. Rebuilt and restored databases each contain 3,980 observations and pass 10/10 queries. Official fresh tagged clone remains pending. |
| G2 Code structure | Configurable modular specialists, tools, orchestration and entry points. Local model paths and secrets are supplied through config/environment. Final review against the official template remains pending. |
| G3 Artifacts | Manifest, schema, dictionary, expected queries, evaluation scripts/results and contribution file are local. Obtain approval and publish a stable course-approved adapter location, then record the link and hash. |
| G4 Version control | The required semester contribution history, submission revision and team attribution require the team and TA. |
| Viva and gates | Evaluator-dependent. The working-tree checks do not establish instructor acceptance. |

The [reproducibility report](../evidence/technical_completion/reproducibility.json) records the local clean-room steps. The [live technical checks](live_technical_checks.md) list exact commands and evaluator inputs, including the direct LGD export. See the [source and model rights review](technical_source_rights.md) for publisher follow-ups.
