# Intraday-PulseTrade Run Report

Date: 2026-08-30

This report records the step-by-step execution attempt from `D:\project\Intraday-PulseTrade`.

## Summary

Terraform checks pass. Python is installed and usable locally through the Windows Python Manager alias at `C:\Users\ACER\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.PythonManager_3847v3x7pw1km\python.exe` (`Python 3.14.5`). A project virtual environment was created at `src\.venv`, dependencies installed successfully, source compilation passed, imports passed, and the local Functions Framework handled a test CloudEvent on `http://127.0.0.1:8080`.

`python`, `py`, `git`, `gcloud`, and `docker` are still not available directly on the current terminal PATH. Full historical or CSV incremental execution was not run because those paths create/use Google Cloud BigQuery and GCS resources; this run stayed local-only.

## Step Results

| Step | Command | Result | Notes |
| --- | --- | --- | --- |
| 1 | `Get-Location` | PASS | Current directory is `D:\project\Intraday-PulseTrade`. |
| 2 | `Test-Path README.md`, `.env.example`, `src/main.py`, `src/requirements.txt`, Terraform modules | PASS | All required project files/directories are present. |
| 3 | `terraform -version` | PASS | Terraform `v1.15.8` is available. It reports that `1.16.0` is newer. |
| 4 | `gcloud --version` | FAIL | `gcloud` is not recognized. Google Cloud CLI is missing or not on PATH. |
| 5 | `docker --version` | FAIL | `docker` is not recognized. Docker is missing or not on PATH. |
| 6 | `python --version` | FAIL | `python` is not recognized on PATH. Python was found through the Windows Python Manager alias instead. |
| 7 | `py --version` | FAIL | `py` is not recognized. Windows Python launcher is missing or not on PATH. |
| 8 | `python3 --version` | FAIL | `python3` is not recognized. |
| 9 | `git --version` | FAIL | `git` is not recognized. Git is missing or not on PATH. |
| 10 | `terraform init` in `Terraform/service_account` | PASS | Provider reused from cache. |
| 11 | `terraform init` in `Terraform/bucket` | PASS | Provider reused from cache. |
| 12 | `terraform init` in `Terraform/bigquery` | PASS | Provider reused from cache. |
| 13 | `terraform fmt -check -recursive Terraform` | PASS | Terraform files are formatted. |
| 14 | `terraform validate` in `Terraform/service_account` | PASS | Configuration is valid. |
| 15 | `terraform validate` in `Terraform/bucket` | PASS | Configuration is valid. |
| 16 | `terraform validate` in `Terraform/bigquery` | PASS | Configuration is valid. |
| 17 | `terraform plan -input=false` in `Terraform/service_account` | PASS | Plan: `3 to add, 0 to change, 0 to destroy`. |
| 18 | `terraform plan -input=false` in `Terraform/bucket` | PASS | Plan: `1 to add, 0 to change, 0 to destroy`. |
| 19 | `terraform plan -input=false` in `Terraform/bigquery` | PASS | Plan: `4 to add, 0 to change, 0 to destroy`. |
| 20 | Python alias `--version` | PASS | `Python 3.14.5` via `C:\Users\ACER\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.PythonManager_3847v3x7pw1km\python.exe`. |
| 21 | Python alias `-m venv .venv` in `src` | PASS | Local virtual environment created at `src\.venv`. |
| 22 | `docker build -t intraday-pulsetrade .` in `src` | FAIL | Blocked because `docker` is not recognized. |
| 23 | `gcloud config list` in `src` | FAIL | Blocked because `gcloud` is not recognized. |
| 24 | `.\.venv\Scripts\python.exe --version` in `src` | PASS | Virtual environment uses `Python 3.14.5`. |
| 25 | `.\.venv\Scripts\python.exe -m pip --version` in `src` | PASS | `pip 26.1.1` is available inside `src\.venv`. |
| 26 | `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` in `src` | PASS | Installed Functions Framework, Google Cloud Storage, Google Cloud BigQuery, and dependencies. |
| 27 | `.\.venv\Scripts\python.exe -m pip check` in `src` | PASS | No broken requirements found. |
| 28 | `.\.venv\Scripts\python.exe -m compileall -q historical incremental ingestion main.py transform utils validation` in `src` | PASS | Source-only syntax compilation passed. |
| 29 | Import smoke test for runtime modules | PASS | `functions_framework`, `google.cloud.storage`, `google.cloud.bigquery`, `main`, `historical`, `incremental`, and `transform.bronze` imported successfully. |
| 30 | Historical loader local control-flow smoke test | PASS | Ran `run_historical()` with `process_historical_month` stubbed locally to avoid GCP calls. |
| 31 | Incremental entrypoint local control-flow smoke test | PASS | Tested non-CSV skip and CSV handoff with `run_incremental` stubbed locally to avoid GCP calls. |
| 32 | Functions Framework local server | PASS | Started after overriding `DEBUG=false` for the process; served on `http://127.0.0.1:8080`. |
| 33 | Local CloudEvent POST to Functions Framework | PASS | `Invoke-RestMethod` returned `OK` / HTTP 200 for `notes.txt`, which avoided the BigQuery path. |

## Local Python Steps

These steps now pass locally:

```powershell
cd src
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m compileall -q historical incremental ingestion main.py transform utils validation
```

These steps were not run against live CSV/GCP resources because this run was local-only and did not perform remote cloud work:

```powershell
cd src
.\.venv\Scripts\python.exe -m historical.historical_loader
functions-framework --target=process_new_csv --signature-type=cloudevent --port=8080
# followed by a CSV CloudEvent, which would call BigQuery/GCS
```

These steps were not run because Docker is unavailable:

```powershell
cd src
docker run --rm -p 8080:8080 intraday-pulsetrade
```

These steps were not run because Google Cloud CLI is unavailable:

```powershell
gcloud auth login
gcloud auth application-default login
gcloud config set project project-001658fa-3ce5-4746-980
gcloud functions deploy process-new-csv ...
```

`terraform apply` was not run intentionally because it creates or changes Google Cloud resources.

## Next Required Fixes

1. Optional: add Python to PATH so `python` works directly, or keep using `src\.venv\Scripts\python.exe`.
2. Install Google Cloud CLI and authenticate with the target project before running the real GCP-backed pipeline.
3. Install Docker Desktop if containerized local execution is required.
4. Install Git for normal repository inspection and version control.
5. For local Python-only validation, use the venv directly:

```powershell
cd D:\project\Intraday-PulseTrade\src
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m compileall -q historical incremental ingestion main.py transform utils validation
```

6. After Google Cloud authentication is available, run the historical loader or Cloud Function local test from the README.

## Update: 2026-09-04

The project was updated for scoped incremental processing:

- Incremental Bronze now derives the uploaded file's symbol and timestamp range from the staging table.
- Silver receives that scope and filters Bronze early, while keeping a 100-day lookback for indicator calculations.
- Gold receives the same scope and limits intraday metrics, signals, and daily facts to the uploaded symbol/date where possible.
- Gold runtime logging now prints start time, end time, elapsed time, Silver input counts, Gold output counts, and Semantic view counts.
- Semantic view documentation now reflects the current dashboard views:
  `vw_current_intraday`, `vw_stock_metrics`, `vw_scanner`, `vw_current_breakouts`, `vw_top_gainers`, `vw_top_losers`, `vw_latest_daily`, `vw_stock_returns`, and `vw_market_overview`.
- The recommended Cloud Function deployment is now single-concurrency with `--timeout=540s`, `--memory=2Gi`, `--cpu=1`, `--concurrency=1`, and `--max-instances=1`.

Known indicator caveat:

- Silver `sma_20` and `vwap` are standard SQL calculations.
- Silver `ema_9`, `ema_20`, `rsi_14`, `macd`, and `macd_signal` are rolling-window approximations, not true recursive technical indicator formulas.
