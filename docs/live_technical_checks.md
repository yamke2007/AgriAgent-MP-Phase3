# Live technical checks

Run these commands from the repository root in PowerShell. Use a review checkout and source access approved by the TA. Complete the setup and smoke tests before receiving surprise inputs. No settings or code changes are needed while the inputs run.

## Instructor items and reference review

1. Ask the TA for the official metrics CSV template and three unseen source items, including at least one in Hindi. Ask the TA to keep the independently checked 10–15-field answer key for each item until extraction finishes.
2. Run the first command below in the files' declared order. Keep the capture, trace JSONs and automation CSV. Count any configuration or manual handling required by the protocol in the three corresponding `--manual-interventions` values.
3. Save the TA's answer key as a JSON array of three objects in input order. Each object has `language`, `records` with official field tuples and, when known, `input_sha256`. Supply the reference `agent` and `source_group` for each item when available, especially for inputs the router could fail to classify. Score the saved capture with the second command.
4. Give the independent reviewer `output/reviewer_queue.csv`, the original parents and the matching rules in `eval/README.md`. Check inputs and source locators against original cells, correct discrepancies in a versioned reference set, and record reviewer identity, date and decision. Preserve frozen M18 references and original scores if a separately revised reference set is needed.

```powershell
$py = '.venv-clean/Scripts/python.exe'
& $py eval/run_surprise.py 'C:/demo/item1.pdf' 'C:/demo/item2-hi.pdf' 'C:/demo/item3.csv' --output output/live-surprise
& $py eval/run_surprise.py --score-existing --key 'C:/demo/checked-key.json' --output output/live-surprise
```

The first command saves `surprise.json` with blank M5 and digests of the three original run files. The second verifies these digests and writes `surprise-scored.json`, with per-item, per-agent, per-source-group, pooled and equal-agent macro F1. Use a fresh output path for each new set. This harness attempts unsupported formats and records the resulting failure.

## LangSmith and fault recovery

1. Create an API key in the team's approved LangSmith workspace. Set the variables below in the demo shell. Set the endpoint and workspace ID to the values from LangSmith if the workspace requires them. Use PowerShell 7 for the masked prompt. Trace the public DES report below. Keep instructor files local unless the TA approves sharing them with LangSmith.
2. Run the command below after the DES PDF is available and hash-checked by the existing acquisition tooling. Open the project in LangSmith, locate the supervisor run, show the statistics-to-tables hand-off, the failed tool invocation and successful retry. Save the trace URL and observed outcome. Show the detailed tool trace from the local run artifact alongside it.
3. Clear the key and turn off tracing before processing restricted files.

```powershell
$env:LANGSMITH_API_KEY = Read-Host 'LangSmith API key' -MaskInput
$env:LANGSMITH_TRACING = 'true'
$env:LANGSMITH_PROJECT = 'agriagent-live'
$env:LANGSMITH_HIDE_INPUTS = 'true'
$env:LANGSMITH_HIDE_OUTPUTS = 'true'
@{
  database='output/live-fault/agriagent.sqlite'
  output_dir='output/live-fault/runs'
  automation_log='output/live-fault/automation.csv'
} | ConvertTo-Json | Set-Content -Encoding utf8NoBOM output/live-fault-config.json
& $py run.py --input output/source-expansion/acquisition/S12_major_report.pdf --config output/live-fault-config.json --inject-tool-fault pdfplumber.extract_tables --trace
$env:LANGSMITH_TRACING = 'false'
Remove-Item Env:LANGSMITH_API_KEY
```

Expected local outcome is 52 records and one retry. The supervisor and LangGraph trace provide remote workflow evidence when credentials and network access are available. The local trace retains application-level tool arguments, faults and retry details. Confirm both artifacts live. [LangSmith SDK reference](https://reference.langchain.com/python/langsmith)

## Evaluator-selected provenance and queries

1. Open the database schema and dictionary. Ask the evaluator to select three observation IDs. For each ID run the command below, substituting that ID. Record the three outcomes individually for M17.
2. Use the source URL, hash, input path and locator in each result to open the original source. For derived observations follow `origin_source` and `origin_locator` as well. Resolve archived paths by SHA-256 in `data/manifest.csv`.
3. Run `list`, then run each query q01–q10 individually in front of the evaluator. Ask them to check the answers and categories. For q10 open the cited physical PDF page and locate the quoted figure. Run `verify` to save the machine comparison to expected results too.

```powershell
& $py scripts/db_cli.py --database output/release/agriagent.sqlite --id 1
& $py scripts/query_release.py list
1..10 | ForEach-Object { & $py scripts/query_release.py ('q{0:00}' -f $_) }
& $py scripts/query_release.py verify --output output/live-query-verification.json
```

## Direct LGD register

Open the Ministry [Download Directory](https://lgdirectory.gov.in/downloadDirectory.do). Select the district directory and Madhya Pradesh. Complete the on-screen CAPTCHA yourself, generate the XLS or HTML report and retain that original with its download date and URL. If the portal offers XLS, open the district table in Excel and save it as CSV UTF-8, keeping the English district name and district LGD code columns. Retain state columns if published. Record the raw export SHA-256 using `Get-FileHash`. If offered HTML only, use the browser's download and copy the rendered table to Excel, retaining its column names and rows. Reconcile any difference against the raw report before building the registry. Use the explicit MP-only switch only for an export scoped to MP.

```powershell
Get-FileHash 'C:/demo/lgd-mp-original.xls' -Algorithm SHA256
& $py scripts/verify_lgd_join.py 'C:/demo/lgd-mp.csv' --mp-only-export --source-url 'https://lgdirectory.gov.in/downloadDirectory.do' --output output/lgd-ministry-verification.json
& $py scripts/import_lgd.py 'C:/demo/lgd-mp.csv' --mp-only-export --no-config --out output/lgd-mp-registry.json
```

The audit opens the release database read-only. Add the registry to a new rehearsal configuration after review. The 52 historical polygons and 55 current districts have different administrative vintages.

## Fresh setup, rebuild and restore

Use Python 3.12, PowerShell 7 and Tesseract with the `eng` and `hin` language packs on the verifier's machine. Put the Tesseract binary on PATH, set `TESSDATA_PREFIX` to the directory containing the packs if needed, and run `tesseract --list-langs`. Download only corpus files approved for the review environment and verify their hashes. The core commands below use separate paths.

```powershell
py -3.12 -m venv .venv-ta
$py = '.venv-ta/Scripts/python.exe'
& $py -m pip install -r requirements.txt
& $py -m pip check
& $py scripts/build_release.py --output output/ta-rebuild
& $py scripts/query_release.py verify --db output/ta-rebuild/agriagent.sqlite
& $py scripts/db_cli.py --database output/ta-rebuild/agriagent.sqlite --dump --dump-dir output/ta-backup
& $py scripts/restore_release.py output/ta-backup/agriagent.sql output/ta-restored.sqlite
& $py scripts/query_release.py verify --db output/ta-restored.sqlite
& $py -m unittest discover -v
```

Ask the TA to record each setup step completed without help, record any required fixes, and repeat from the approved submission checkout when available.

## Adapter pipeline on Windows CPU

Use a dedicated Python 3.12 environment. Extract the verified Colab export before running this check. The download requires about 3.1 GB of disk space for the base weights. Generation can take several minutes on a CPU.

```powershell
py -3.12 -m venv .venv-adapter
$mpy = '.venv-adapter/Scripts/python.exe'
& $mpy -m pip install -r requirements.txt
& $mpy -m pip install 'torch==2.7.1' --index-url https://download.pytorch.org/whl/cpu
& $mpy -m pip install 'transformers==4.57.1' 'peft==0.17.1' 'accelerate==1.11.0'
& $mpy -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen2.5-1.5B-Instruct',revision='989aa7980e4cf806f80c7fef2b1adb7bc71aa306',local_dir='output/qwen-base',allow_patterns=['*.json','*.txt','model.safetensors','LICENSE'])"
Get-FileHash output/qwen-base/model.safetensors -Algorithm SHA256
Get-FileHash output/m18/adapter/adapter_model.safetensors -Algorithm SHA256
@{
  model_path='output/qwen-base'
  adapter_path='output/m18/adapter'
  database='output/ta-adapter-check/agriagent.sqlite'
  output_dir='output/ta-adapter-check/runs'
  automation_log='output/ta-adapter-check/automation.csv'
} | ConvertTo-Json | Set-Content -Encoding utf8NoBOM output/ta-adapter-config.json
$env:HF_HUB_OFFLINE = '1'
& $mpy run.py --input eval/cases/tables_14_agmarknet_soyabean_2013.csv --config output/ta-adapter-config.json --trace
```

The expected base SHA-256 is `dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee`. The expected adapter SHA-256 is `589b4c8bce67b16b82bfb102b887d9f754db875151bc008378c4e7e2e867571d`. Check for a successful `llm.peft_extraction` tool event, recorded token usage and source-resolved records marked `model_confirmed`. A fallback is useful for the application and does not count as adapter integration evidence. [Pinned checkpoint](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct/blob/989aa7980e4cf806f80c7fef2b1adb7bc71aa306/model.safetensors)
