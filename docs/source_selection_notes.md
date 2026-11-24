# Source Selection Notes — Phase 1 TA Review
**Review date:** 24 October 2026

## Files and evidence reviewed
- Original `Source_Inventory/source_inventory.csv` (23 source rows, 9 columns).
- Original `Source_Inventory/MP_Source_Inventory.xlsx` (one worksheet, 23 rows, same 9-column inventory structure).
- `docs/Phase1/Crop_and_Stage_Scope.md`
- `docs/Phase1/Phase1_Report.md`
- `docs/Phase1/Source_Analysis.md`
- `docs/Phase1/Problem_Statement.md`
- `docs/Phase1/Phase1_Evaluation_Mapping.md`
- `docs/Phase1/Agent_Tool_Plan.md`
- `logs/source_verification_log.md`
- **No separate evaluation/protocol PDF was present inside the supplied ZIP or alongside it in the mounted upload directory.** This deliverable therefore uses the existing repository documents as primary evidence.

## Selection criteria
1. Match to an information point explicitly named in Phase 1.
2. Directness: a relevant page, document or query endpoint is preferred to a portal home page that links to more systems.
3. Official ownership and state/district/crop/time relevance.
4. Visible, usable modality and reasonable accessibility.
5. Complementarity: avoid treating multiple pages from the same system as separate evidence of broad coverage.
6. Data minimization: no unnecessary personal or beneficiary-level farmer data.
7. Honest verification: a URL appearing in the inventory is not, by itself, evidence of a current successful check.

## Core and supporting selection
- **Core primary candidates:** MP e-Vikas fertilizer calculator (farm planning/input recommendation); DES APY query (production statistics); IMD crop advisory (field monitoring); ICAR Madhya Pradesh KVK directory (extension institution lookup).
- **Conditional primary candidate:** MP e-Uparjan. Official Madhya Pradesh district pages point to the current-looking portal path, but public access to the exact quantitative fields required by the team has not been established.
- **Descriptive/policy sources:** MP CM Helpline MSP procurement scheme page and PMFBY guidelines; useful for rules/process, not a substitute for operational procurement or insurance statistics.
- **Backups:** DES Agricultural Statistics at a Glance for published tables; e-Mandi manual for system workflow; e-NAM for mandi coverage/status only until commodity-level price/arrival fields are demonstrated.
- **Deferred:** PMFBY administrative dashboard, machinery service portal, e-Services directory, e-NAM online and unified-license pages, historical survey/telephone PDFs until their exact value is confirmed.
- **Excluded from current data target:** PM-KISAN beneficiary list, because it contains person-level beneficiary lookup information and is unnecessary for the current crop-stage scope.

## Deduplication and count interpretation
- Original inventory: 23 rows.
- Cleaned mapping: one row per source × proposed stage × mapped information-point label. A source may therefore appear more than once in `cleaned_source_inventory.csv`; this is intentional and is not a count of separate original sources.
- Frequency summary groups related inventory entries into 15 source families (for example, the two e-Vikas entries and the three DES APY/statistics entries are not treated as independent systems).
- Coverage counts are normalized labels mapped from the inventory descriptions and existing scope documents. They are not counts of source records, extracted facts, confirmed downloadable fields, or verified crop-stage combinations.
- No crop source is assumed to support all six proposed crops. Crop-specific availability must be confirmed against the actual interface or report.

## Link verification record
Substantive page content was observed via web search/open results on 24 October 2026 for:
- MP e-Vikas home and fertilizer calculator.
- DES APY query.
- IMD crop advisory (a dated advisory page was visible).
- e-Anugya/e-Mandi home and its user-manual PDF.
- DES Agricultural Statistics at a Glance official reports index.
- ICAR Madhya Pradesh KVK directory.
- e-NAM mandi status.
- PMFBY official home page (the exact inventory `/guidelines` URL was not separately confirmed).

Partial check:
- e-Uparjan: current-looking portal link is referenced by official MP district-administration pages, but the inventory's original HTTP home URL was not directly re-tested and the relevant public output fields remain unconfirmed.

Not individually checked in this review:
- MP CM Helpline MSP scheme URL, MP e-Services, MP Directorate of Agricultural Engineering and farmer machinery portal, DES major-district APY report, PMFBY administrative dashboard, PM-KISAN pages, e-NAM online and unified-license pages, ICAR 2020 telephone PDF, MP Economic Survey PDF.
These retain the status “not checked” or “partial” in the cleaned inventory. The source inventory's pre-existing `VERIFIED` labels have not been silently treated as fresh verification.

## Known limitations / deferred sources
- **Portals:** MP e-Services is a service directory that links to separate systems; e-Vikas distribution, e-Uparjan, e-NAM, PMFBY dashboard and machinery portals may require filters, browser interaction or login. Do not select them as primary for a data field until the field can be reached directly.
- **Duplicates/overlap:** e-Vikas calculator + distribution portal; e-Anugya home + manual; DES APY query + major district view + annual statistics; PMFBY guidelines + dashboard; e-NAM status + online + license; ICAR directory + older telephone PDF. They have different roles, but should be grouped as source families in the frequency summary.
- **Historical:** ICAR KVK telephone directory is from 2020; MP Economic Survey highlights are 2022–23. Use only with their time label and not as current contact/statistics claims.
- **Data types:** The two CSV/Excel files are inventory metadata, not agriculture datasets. No direct JSON/API or image dataset is established in the supplied inventory.
- **Crop coverage:** The six crops are proposed globally; individual source crop support remains unverified unless the interface visibly supports it and is tested.
- **Terms/licensing:** The inventory does not provide verified licenses or data-use permissions. No license claim is made here; check source terms before any later automated collection.

## Questions to take to the TA
1. Are all six proposed crops (soybean, wheat, gram/chickpea, maize, rice/paddy, cotton) required, or may the team narrow the initial scope?
2. Should the first demonstrable scope prioritize five practical areas—fertilizer/farm planning, advisories, production, procurement and market/logistics—or retain all seven proposed activity stages?
3. Are cross-cutting schemes, crop insurance and KVK/extension directory facts required in the same scope, or should they be treated as supporting information only?
4. Which market fields are mandatory: arrivals, minimum/maximum/modal price, mandi and date? The current inventory does not prove a single direct source supplies all fields.
5. What counts as sufficient source access for the TA: a direct static page/document, or is an interactive query page acceptable if it exposes the relevant result without account login?
6. Must sources cover all six crops, or is source coverage allowed to vary by crop and information point?

## Boundary
No Phase 2 work was performed. No new agent, extraction pipeline, evaluation script, model adapter, or database functionality was created. Original inventory files were preserved unchanged.
