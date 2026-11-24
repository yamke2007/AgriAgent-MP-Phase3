# Phase III manuscript outline and evaluation crosswalk

The official project methodology, Phase II protocol, and Phase III evaluation grid were read in full. The grid requires 15–20 pages, IEEE-style references, at least 12 sources, readable captioned figures, and the course template with Tables 1–2. The separate manuscript template and the Phase II CSV attachment are absent. Table numbering and layout below are provisional until the team supplies them.

| Sequence | Manuscript content | Official criterion and evidence |
| --- | --- | --- |
| 1 | Title, abstract, keywords | R1/R5. State, implemented task, evaluation cohorts, key findings and limits. Roster names follow the Phase I charter pending spelling and author order confirmation. |
| 2 | Introduction, problem, objectives and scope | R1. Explain heterogeneous Hindi and English sources, retrieval barriers and source-to-answer traceability. Show 23 mapped and 14 scoped implementations, without implying state-wide live coverage. |
| 3 | Background and related work | R1. Synthesise government information infrastructure, document extraction, agent workflows, provenance, LoRA/QLoRA and model evaluation. Use 12 or more primary sources, cited in text. |
| 4 | Information sources and corpus preparation | R2. Provisional Table 1 documents supported source families, provenance and scope. Explain the 135-file manifest, dispositions and acquisition checks. |
| 5 | Architecture, orchestration and individual agents | R2. Provisional Table 2 specifies agents, tools, inputs, outputs, decisions and failure modes. Draw routing, hand-off, retry, guard and storage diagrams. Separate fixed code from learned behaviour. |
| 6 | Extraction, validation, provenance and SQLite | R2/R4. Describe context keys, normalisation, units, missingness, foreign keys, eligibility, and source locators. Use actual DES and LGD checks. |
| 7 | QLoRA fine-tuning | R2/R3. Pin the checkpoint and training recipe, describe the temporal split, compute budget, adapter, clean held-out inference and tuple matching. |
| 8 | Phase II evaluation and M1–M18 | R3 and Phase II protocol. Give denominators, per-agent and per-source-group results, equal-agent macro-aggregation, genuine-input M12, M11 cohort and separate fault test, M18 precision/recall/F1 and error counts. Mark M5 and M17 pending. |
| 9 | Phase III query system | R3 and methodology gate. Catalogue all ten queries by category, result size and example. Report ordered local verification on the original/rebuilt/restored database and the still-pending live check. |
| 10 | Geospatial and temporal analysis | R3/R5. Define area-weighted yield, balanced panel, paired correlations, eligibility and map joins. Use extant charts/maps by reference in an opt-in local build. Default build uses original vector figures showing aggregate statistics. |
| 11 | Reproducibility, automation and faults | R2/R3/R4; technical evidence relevant to G1–G3. Cover Windows setup, backups, repeated runs, DES sampled values, trace status and artifact integrity. |
| 12 | Limitations, ethics, future work, conclusion and references | R4/R5. Separate method limits, source limitations and implementation limits. Document licensing, privacy, the three pending evaluation elements, authorship and release conditions. |

R1 is worth 0.25, R2 is worth 1.00, R3 is worth 1.25, R4 is worth 0.50 and R5 is worth 1.00, for a total of 4.00 report marks. The draft reports empirical results and leaves grading to the evaluator. Poster, presentation, user manual and video are outside this deliverable.

## Final confirmation

- Provide the exact report template, its Tables 1–2, and the official Phase II CSV attachment if available.
- Confirm team ID, authors' display names/order, institutional affiliation line, and actual contributions. Follow the course filename convention once the team ID is confirmed.
- Retain the approved LangSmith evidence and record instructor acceptance only after the actual evaluations.
- Confirm display and redistribution permissions for the exact retained charts, historical layer, maps and animation before including those original assets in a deliverable that leaves the local review environment.
