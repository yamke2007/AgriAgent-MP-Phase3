# TA Scope and Source Selection — AgriAgent Madhya Pradesh
**Phase 1 scope clarification only | Review date: 24 October 2026**

## Purpose and boundary

This note responds to TA feedback that the source inventory is difficult to interpret. It converts the existing Phase 1 proposal into a compact map of **proposed crop activities → specific information points → candidate sources and modalities**. It does not implement retrieval, extraction, agents, evaluation scripts, or database functionality.

The supplied Phase 1 ZIP contains the source inventory and project documentation, but **does not contain a separate evaluation/protocol PDF**. Accordingly, this clarification is grounded in the repository's `Crop_and_Stage_Scope.md`, `Phase1_Report.md`, `Source_Analysis.md`, `Problem_Statement.md`, and original CSV/XLSX inventory.

## 1. Scope at a glance

- **State:** Madhya Pradesh.
- **Proposed crop set (not yet finalized):** soybean, wheat, gram/chickpea, maize, rice/paddy, and cotton.
- **Proposed activity stages:** seed-related information; farm planning; field monitoring/advisories; production; procurement; aggregation, storage and logistics; market and supply chain.
- **Cross-cutting topics already listed in the Phase 1 report:** schemes, crop insurance, and agricultural extension/KVK information.
- **Current artifact:** source discovery and knowledge-base design. The Phase 1 files explicitly do not represent a production agent or populated production database.

### Out of scope for this TA clarification

No Phase 2 implementation; no new extraction pipeline, agent, model adapter, database, or automated evaluation; no collection of Aadhaar-linked or unnecessary person-level farmer data. The PM-KISAN beneficiary list is therefore excluded from the current source set.

## 2. Crop stages and information points

| Proposed stage/activity | Specific information to retrieve (only where the source exposes it) | Key dimensions |
|---|---|---|
| Seed-related information | Seed testing/quality-control service information; seed testing or licensing process where documented | Service, department, location, application/process |
| Farm planning | Crop/area inputs and displayed NPK requirement/fertilizer quantity; fertilizer distribution context; scheme name, eligibility, benefit and application steps; insurance rules | Crop, area, district/state, scheme, season/year |
| Field monitoring/advisories | Dated crop-specific advisory text and recommended actions for weather, crop management, and pest/disease risks when explicitly stated; KVK name/district/host organization for extension discovery | Advisory date, state/district, crop, KVK |
| Production | Cultivated area, production, yield, crop, season, district/state and year | Crop, district/state, season, year |
| Procurement | Procurement scheme purpose/process; crop/season and procurement-centre information where publicly exposed; published procurement statistics where a report contains them | Crop, procurement season, centre, year |
| Aggregation, storage and logistics | Mandi/APMC and procurement-centre references; e-Mandi workflow; mandi coverage/status; trading/arrival/price fields only if the selected interface actually exposes them | Mandi, commodity, date, district |
| Market and supply chain | Commodity, mandi/APMC, date, arrivals, minimum/maximum/modal price where a source exposes these fields; market-system and licensing context | Commodity, mandi, date, price/arrivals |

**Important crop-specificity rule:** the six-crop list is a project-level proposal. The inventory does not prove that every source supports every crop. DES APY and the e-Vikas calculator expose crop selection in their interfaces; each target crop must still be checked individually. For other sources, crop coverage remains unconfirmed unless a source page or result explicitly names the crop.

## 3. Prioritized source shortlist

“Link checked” means the linked page or its substantive content was opened/observed during this review, not merely copied from the inventory. “Direct” means a specific page/document/query endpoint, not a claim that every result can be downloaded without interaction.

| Priority | Source / owner | Direct link | Stage and information points | Modality | Status / reason |
|---|---|---|---|---|---|
| 1 | **MP e-Vikas fertilizer calculator** — MP Department of Farmers Welfare & Agriculture Development | [Open calculator](https://evikas.mpkrishi.mp.gov.in/OFRDHome/FarmerFertilizer_Calculator) | Farm planning: crop and area inputs, displayed NPK requirement, fertilizer product/quantity options | Dynamic HTML/web calculator; page content observed | **Primary; checked 24 Oct 2026.** Closest direct match for fertilizer recommendation. Interactive output; manually test target crops. |
| 2 | **DES Area, Production & Yield (APY) query** — Government of India, Agriculture & Farmers Welfare | [Open APY query](https://data.desagri.gov.in/website/apy-query-report-web) | Production: area, production, yield by state/district/crop/season/year | Dynamic HTML query form; page content observed | **Primary; checked 24 Oct 2026.** Direct query endpoint with relevant dimensions; output needs manual sampling. |
| 3 | **IMD crop-specific advisory** — India Meteorological Department | [Open crop advisory](https://imdagrimet.gov.in/cropAdvisory_3.php) | Field monitoring: dated crop-specific advisory text and recommended actions | Dynamic HTML/advisory page; dated advisory observed | **Primary; checked 24 Oct 2026.** Direct advisory page; state/district filters and history need checking. |
| 4 | **ICAR Madhya Pradesh KVK directory** — Indian Council of Agricultural Research | [Open MP KVK directory](https://icar.gov.in/en/node/15044) | Field monitoring/extension: KVK name, district, host organization, sanction year | HTML table; page content observed | **Primary for extension-directory facts; checked 24 Oct 2026.** Direct table; directory freshness should be confirmed. |
| 5 | **MP e-Uparjan** — Government of Madhya Pradesh | [Open current MP district-linked portal](https://mpeuparjan.nic.in/mpeuparjan/Home.aspx) | Procurement: process and procurement-centre/season information where public | Dynamic web portal | **Primary candidate; partially checked.** Official MP district pages point to this URL, but publicly extractable quantitative data was not established. Do not rely on it for figures until tested. |
| 6 | **MP MSP procurement scheme page** — MP CM Helpline | [Open scheme detail](https://cmhelpline.mp.gov.in/Schmedetail.aspx?Schemeid=112) | Procurement/farm planning: scheme purpose and application/process facts | Government HTML page (inventory classification) | **Primary for descriptive scheme facts; inventory URL not re-opened in this review.** Complements, but does not replace, operational procurement data. |
| 7 | **PMFBY guidelines** — Pradhan Mantri Fasal Bima Yojana | [Open official PMFBY site](https://pmfby.gov.in/guidelines) | Farm planning/insurance: scheme rules, coverage, eligibility, application/claim process | Government portal/PDF links (inventory classification) | **Primary candidate for policy facts; exact inventory path not separately confirmed.** Use the current official guideline version and record its date. |
| 8 | **DES Agricultural Statistics at a Glance** — Government of India | [Open official reports page](https://desagri.gov.in/document-report-category/agriculture-statistics-at-a-glance/) | Production/procurement: published annual statistics, only the tables actually present | HTML report index and downloadable PDF reports | **Backup; official reports page checked 24 Oct 2026.** Stable citation source, but large PDFs and national/state-level tables may not fit district-level queries. |
| 9 | **MP e-Anugya / e-Mandi manual** — MP e-Mandi system | [Open user manual PDF](https://eanugya.mp.gov.in/HR/Doc/User_ManualForMandiSecretary.pdf) | Market/logistics: mandi-system workflow and permit/payment process context | PDF; PDF content observed | **Backup; checked 24 Oct 2026.** Direct document, but it is a workflow manual—not a commodity price/arrival dataset. |
| 10 | **e-NAM mandi status** — National Agriculture Market | [Open mandi status](https://enam.gov.in/eNam-mandi-status) | Market/logistics: mandi coverage/status and the fields shown by the selected view | Dynamic HTML interface; page content observed | **Backup; checked 24 Oct 2026.** Direct interface, but not yet proven to supply the required MP price/arrival records. |

The shorter ranked source-family analysis is in `source_frequency_summary.csv`. The full source-by-information-point mapping, including deferred entries and link-check status, is in `cleaned_source_inventory.csv`.

## 4. What the inventory says about frequency and coverage

The original inventory has **23 rows**. Those rows are not all independent sources: several are multiple pages for the same source family (for example, e-Vikas, DES APY, e-NAM, PMFBY and ICAR KVK references). The frequency summary groups these related entries before ranking.

Counts in `source_frequency_summary.csv` are **inventory-derived mapping counts**, not counts of verified records or downloaded datasets:
- “Original inventory entries” counts distinct rows from the supplied inventory grouped by source family.
- “Distinct information points” counts normalized information-point labels mapped from the existing inventory descriptions and Phase 1 scope. It does not mean the source was proven to provide every field.
- “Crop stages” counts the proposed stage labels mapped to the source's described purpose. It does not establish that every crop-stage combination is available.
- Ranking considers relevance and directness as well as coverage. Frequency alone is not used as the selection rule.

## 5. Modalities actually represented

| Modality | Relevant sources | Intended information | Inspection status |
|---|---|---|---|
| Dynamic HTML / web query or calculator | e-Vikas calculator; DES APY; IMD advisory; e-Uparjan; e-NAM | Fertilizer recommendation, area/production/yield, advisory text, procurement/market information | Direct page content confirmed for e-Vikas, DES APY, IMD and e-NAM. e-Uparjan only partially checked. Query outputs and filters still require sampling. |
| HTML table / directory | ICAR MP KVK directory | KVK name, district, host organization, sanction year | Direct table observed 24 Oct 2026. |
| PDF | e-Mandi user manual; DES annual reports; ICAR 2020 telephone directory; MP Economic Survey highlights | Workflow/process context, published annual statistics, historical contacts, historical state indicators | e-Mandi manual content and DES report index checked; the other PDFs were not individually opened in this review. Treat their detailed table contents as unverified until inspected. |
| Government service directory / linked systems | MP e-Services agriculture directory | Discover seed/soil/input testing, machinery subsidy and crop-arrival/rate services | Inventory-described; direct entry not independently re-opened. It is a discovery directory, not the underlying dataset. |
| Dynamic dashboard / form-based portal | PMFBY administrative dashboard; machinery services; fertilizer distribution portal | Aggregated insurance indicators or service/process information where publicly exposed | Inventory-described; not confirmed as directly extractable in this review. |
| CSV/Excel | Original `source_inventory.csv` and `MP_Source_Inventory.xlsx` | Source metadata only (name, URL, modality, language, coverage, limitations, status) | Both provided inventory files were inspected; neither is a crop-production dataset. |
| JSON/API or image data | No source in the supplied inventory is documented as a confirmed direct JSON/API dataset or standalone image dataset | None selected at this stage | **Not established.** Do not claim API/image support based on the current inventory. |

## 6. Open decisions for the TA

1. **Confirm the six-crop scope:** soybean, wheat, gram/chickpea, maize, rice/paddy and cotton, or approve a smaller first cut.
2. **Confirm whether all seven activity stages are required** now, or whether the initial source shortlist should focus on farm planning, field monitoring/advisories, production, procurement and market/logistics.
3. **Confirm the minimum required market fields:** the Phase 1 report names mandi, date, arrivals, minimum, maximum and modal price “where available”; it does not prove that one selected portal exposes all of them directly.
4. **Confirm how to handle cross-cutting topics:** schemes, insurance and KVK/extension are in the Phase 1 report but are not crop stages in the same sense as sowing/field monitoring/harvest.
5. **Confirm source-specific crop coverage and preferred language:** several portals are Hindi-first or dynamic; availability for all six crops and English output is not yet established.
6. **Agree the verification threshold:** the inventory's old “VERIFIED” label records prior preparation status, but the repository's own verification log says links should be re-opened before submission. This review only rechecked the links explicitly marked above.

## 7. Decision recommendation for this review

For a clean TA discussion, present the core shortlist as **e-Vikas calculator, DES APY query, IMD crop advisory, ICAR MP KVK directory, and e-Uparjan (conditional on public access)**. Add the MP procurement scheme page and PMFBY guidelines only for descriptive policy/insurance facts, and keep e-Mandi/e-NAM as supporting market-system sources until actual target fields are demonstrated. Use DES annual reports as a stable backup for published statistics. Keep beneficiary-level PM-KISAN data out of scope.

This is a Phase 1 scope/source clarification only. No Phase 2 functionality has been built.
