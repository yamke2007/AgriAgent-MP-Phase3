# Technical submission readiness

24 November 2026. The technical working tree is ready for a controlled review. Final GitHub publication depends on corpus rights, a submission-file review of the inherited history, and the team's approvals. The current checkout contains one import commit and pre-existing project changes.

## Verified evidence

| Check | Result |
| --- | --- |
| DES PDF and storage | 52 records in 4.66 seconds, 52 stored observations, 5/5 sampled values matched at the original page 1, table 1 locators. |
| Fault recovery | The 7.73-second run logged the hand-off, one injected tool failure, a successful retry, 52 records and zero final errors. A separate repeat in the same database produced 52 duplicates and added zero observations. |
| Remote LangSmith | The owner reports viewing the supervisor, hand-off and retry. The local trajectory supports those events. No remote trace URL or export was available for this review. |
| Direct ministry LGD | The retained workbook, CSV and generated registry agree on 55 codes and names. The read-only recheck matched 52/52 historical release districts, 1,886/1,886 panel rows and 52/52 map districts. The registry is `output/lgd-mp-registry.json`. |
| Trained adapter | Pinned base and adapter SHA-256 values matched. The laptop tool call succeeded in 276.78 seconds and confirmed 4/16 fields. It returned zero unmatched predictions and a partial run. Case recall was 25%. The separate ten-case Colab M18 remains +0.677419 F1, with 52.50% adapter recall. |
| Backup and queries | The laptop SQL dump restored to memory with SQLite integrity and foreign-key checks passing. Its existing restored database has 3,980 observations. All ten queries passed on both the local release and the laptop-restored database. |
| Final regressions | 62/62 passed with English and Hindi OCR installed. |
| Preservation | All 33 protected artifacts match the earlier digest list. All 135 corpus-manifest entries exist and match their SHA-256 values. |

[Laptop checks and hashes](../evidence/final_submission/laptop-verification.json) · [Regression log](../evidence/final_submission/regression.txt) · [Original metric snapshot](../evidence/technical_completion/phase2_metrics.csv)

## Repository review

- **README and dependencies.** Use the technical release section. It covers Python 3.12, dependency installation, OCR, extraction, queries, backup/restore and optional model setup. The earlier sections document historical checkpoints. The [verified dependency versions](../evidence/technical_completion/fresh_pip-freeze.txt) supplement `requirements.txt` and the separate Colab pins.
- **Configuration.** The default, demo and fault configs use relative paths. Model and registry paths are supplied locally. Credentials belong in the environment. The reviewed application source has no hardcoded user directory.
- **Corpus and database.** Keep the manifest, lineage metadata, schema, dictionaries and query expectations with the technical submission. Before GitHub publication, clear the rights for source bytes, query fixtures containing source excerpts, and database payloads derived from those sources. The local release and SQL dump remain usable for authorized review.
- **Evaluation.** Use the latest versioned evidence and maintain prior snapshots as local history. The standard instructor CSV template was unavailable. The previous top-level evaluator CSVs reflect older checkpoints.
- **Contributions.** `CONTRIBUTIONS.md` awaits confirmation from the real team members. Record their actual roles and evidence before submission. The import commit cannot establish authorship.
- **Credentials and paths.** A pattern scan of current candidate text and the existing Git commit found no matching credential strings. This was a targeted scan. Machine-specific paths were found in historical logs and generated environment evidence. Keep those originals local, and use reviewed summaries for sharing.

## GitHub inclusion and local retention

Use the [exact path inventory](submission_files.csv). `include` means suitable for the technical GitHub review set, subject to course rules. `review` means verify source rights, team privacy, or permitted course distribution before inclusion. `local_only` means retain in the authorized local evidence archive. Check the staged file list against these statuses before any later publication.

The inherited commit already tracks source snapshots, raw traces, database and SQL files. The ignore rules apply to future additions. They do not remove tracked content or prevent its existing history from being shared. Before publishing, confirm that history is approved for the destination or ask the TA which permitted packaging method to use. A clean technical checkout also needs approved access to the required source inputs. Keep the approved handoff instructions and checksums with the code.

| Local material | Reason to retain outside the GitHub review set |
| --- | --- |
| `.venv/`, `.venv-clean/`, `.venv-m18/` and `output/verification/phase3-fresh-venv/` | Installed and machine-specific environments. Recreate from requirements and the verified package list. |
| `output/verification/qwen-989aa79/` | Downloaded checkpoint and model cache. The base weight file alone is 3.09 GB. Keep the pinned revision and checksum in documentation. |
| `output/m18/adapter/` and `output/agriagent-m18-results.zip` | Verified run and trained weights. Retain both. Publish a stable course-approved link and hash if the team and course confirm the rights. |
| `AgriAgent-pre-implementation.zip`, earlier Colab ZIPs, scratch verification copies and repeated release/dump directories | Useful recovery or comparison copies. Redundant for GitHub. |
| `output/personal-*`, raw traces, notebooks with execution output, backups, SQLite files and temporary outputs | May contain source data, local paths or identifying evidence. Keep the final reviewed summaries. |
| `output/lgd-mp-original.xlsx`, `output/lgd-mp.csv`, `output/lgd-mp-registry.json` | Official verification evidence. Confirm terms for the exact download before redistribution. |
| `output/analysis/` and underlying historical geometry | Retain the charts, maps and animation. Exact-layer redistribution and derivative publication still require review. |
| Course PDFs, API keys, local configs containing secrets, browser network exports and trace links | Keep course material and sharing-sensitive evidence in approved locations. The repo can reference the existence and scope of that evidence. |

See the [source rights review](technical_source_rights.md) for publisher-specific terms and the [technical audit](technical_acceptance_audit.md) for phase-by-phase acceptance.

Redundant for submission are the baseline archive, older Colab input bundles under `output/colab*` and `output/m18-gpu-ready`, the prior release under `output/release-before-byte-recovery`, and scratch checkout copies under `output/verification`. Keep the verified M18 ZIP, direct LGD workbook, and at least one tested release backup in the local evidence archive.

## Remaining blockers

1. **M11 and live evidence.** Keep the reported LangSmith run link or a redacted export in the approved workspace. The frozen local mixed cohort remains 1/2. The successful fault run is separate evidence. The live evaluator check remains open.
2. **M12 and data availability.** The matched genuine cohort remains 11/17 (64.7%), below the 80% target. Publisher omissions, the CAPTCHA-protected report and unavailable e-NAM results remain unresolved.
3. **Adapter recall and review.** The observed local adapter returned only four of sixteen reference fields. Independent review of source labels, trajectories and held-out references is pending.
4. **Instructor and team requirements.** Obtain the CSV template, three unseen items and checked key for M5, three selected rows for M17, live ten-query and clean-machine verification, contributor confirmations, and instructor acceptance.
5. **Publication clearance.** Confirm rights and approved delivery for the DES-origin mirror and PDFs, Agmarknet corpus and related artifacts, registry, historical geometry and derived visualizations. Confirm the distribution of inherited Git content and the adapter link before GitHub publication.
