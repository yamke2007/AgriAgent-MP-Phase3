# Building the manuscript

The default build uses original diagrams and aggregate plots. It does not embed the repository's restricted source PDFs, raw corpus, stored maps, trained weights or animation. Run from this directory:

```powershell
tectonic manuscript.tex
```

For an authorized local review only, use the optional wrapper below. It references the existing wheat yield chart, the maize/soybean scatterplot and two historical map frames at their repository paths. It does not copy those files. Keep the resulting PDF local until the permissions for the exact assets are confirmed.

```powershell
tectonic local-figures.tex
```

The course grid specifies 15–20 pages and numbered IEEE references. The separate manuscript template and Phase II metrics CSV attachment were absent. The current LaTeX formatting and Tables 1–2 are provisional. See `outline.md` for the evaluation crosswalk and author confirmations.

## Evidence index

| Claim | Repository evidence |
| --- | --- |
| Inventory and extraction scope | `docs/source_agent_map.csv`, `data/manifest.csv`, `evidence/source_expansion` |
| Architecture and schema | `agriagent/orchestrator.py`, `agriagent/tables.py`, `agriagent/pipeline.py`, `db/schema.sql`, `db/dictionary.md` |
| M1–M18 and scope counts | `evidence/technical_completion/phase2_metrics.csv`, `agent_aggregation_check.json`, `m12_paired.json` in the same directory |
| Training, immutable comparison and case errors | `output/m18/configuration.json`, `evidence/m18_release/verification.json`, `adapter_comparison.csv`, `case_scores.csv` in the same directory |
| Query specification and results | `agriagent/queries.py`, `db/queries_expected.json`, `output/final-queries` |
| Crop analysis and original assets | `scripts/analyze_release.py`, `output/analysis/findings.json`, original figures under `output/analysis` |
| Laptop verification, tags of evidence and preservation | `evidence/final_submission/laptop-verification.json`, regression log in the same directory, `docs/submission_readiness.md` |
