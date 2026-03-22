# Garmin Connect Cron Worker

Python worker that:
- Reads tasks from an external source (`ITaskSource`).
- Fetches requested metrics from Garmin Connect using `python-garminconnect`.
- Saves task results.
- Updates each metric date window after successful processing:
  - `from = previous to`
  - `to = (now UTC + 1 day)`

## Structured Requirement

Task object:
- `user_id`
- `token_source`
- `metrics[]`
  - `name`
  - `from` date (`YYYY-MM-DD`)
  - `to` date (`YYYY-MM-DD`)

Abstraction:
- `ITaskSource.get_tasks() -> list[Task]`
- `ITaskSource.save_results(results: list[TaskResult]) -> None`

First implementation:
- `FileTaskSource(task_source, result_source)`
  - Reads: `tasks/{user_id}/task.json`
  - Saves results: `results/{user_id}/result_<timestamp>.json`
  - Updates task range in source file after successful save

## Project Structure

`src/garmin_cron/domain.py` - entities (`Task`, `MetricRequest`, `TaskResult`)  
`src/garmin_cron/interfaces.py` - abstractions (`ITaskSource`, `ITokenProvider`, `IMetricFetcher`)  
`src/garmin_cron/task_sources/file_task_source.py` - file-backed task source  
`src/garmin_cron/token_sources/file_token_provider.py` - token source from disk  
`src/garmin_cron/metrics.py` - Garmin metric adapter  
`src/garmin_cron/services/task_processor.py` - orchestration service  
`src/garmin_cron/main.py` - CLI entrypoint for cron

## Setup

1) Create and activate virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dependencies:

```bash
pip install -r requirements.txt
```

Editable install is optional (works best on newer `pip`):

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -e .
```

3) Configure environment:

```bash
cp .env.example .env
```

4) Create reusable Garmin session tokens (recommended):

```bash
python -m garmin_cron.login --token-source demo-user
```

This stores Garmin auth tokens in `tokens/demo-user/`.

Alternative (legacy) auth file is still supported:

```json
{
  "username": "your-garmin-email@example.com",
  "password": "your-garmin-password"
}
```

5) Add tasks:
- File format: `tasks/{user_id}/task.json`
- Example is already in `tasks/demo-user/task.json`

## Run Once (manual)

```bash
PYTHONPATH=src python -m garmin_cron.main
```

Or:

```bash
./run_worker.sh
```

## Cron Setup

Use `crontab.example` as template:

```bash
crontab -e
```

Add one line (example hourly):

```cron
0 * * * * cd /absolute/path/to/trainer-garminconnect && /absolute/path/to/trainer-garminconnect/run_worker.sh >> /absolute/path/to/trainer-garminconnect/cron.log 2>&1
```

## Supported Metrics

- `steps`
- `heart_rate`
- `sleep`
- `stats`
- `body_composition`
- `activities`

## Authentication Modes

`token_source` in `tasks/{user_id}/task.json` can point to:
- tokenstore directory (recommended): `tokens/<token_source>/`
- credentials file: `tokens/<token_source>.json`
- explicit JSON with tokenstore path:

```json
{
  "tokenstore": "/absolute/path/to/tokenstore"
}
```

## Design Notes (SOLID)

- Single Responsibility:
  - Task retrieval/saving, credential loading, Garmin fetching, and orchestration are separated.
- Open/Closed:
  - Add new task sources by implementing `ITaskSource`.
  - Add new metrics by extending `IMetricFetcher` behavior.
- Liskov Substitution:
  - `TaskProcessor` depends only on interfaces, not concrete classes.
- Interface Segregation:
  - Each interface is focused (`ITaskSource`, `ITokenProvider`, `IMetricFetcher`).
- Dependency Inversion:
  - High-level `TaskProcessor` receives abstractions through constructor injection.

## Issues Found In Original Plan

1) Token source shape was undefined  
- Clarified as file-backed credentials lookup with deterministic resolution rules.

2) Date boundary semantics were ambiguous  
- Defined as inclusive day range and explicit post-run update rule.

3) Error handling/retry policy was not specified  
- Current implementation fails fast for invalid task/token/metric; you may add retries for transient API errors.

4) Result schema was unspecified  
- Added stable JSON result format with execution timestamp and per-metric payload.

5) Security concerns for credentials were not addressed  
- Current baseline uses local files for speed; production should use a secret manager or encrypted storage.

6) Concurrency/duplication behavior under cron was unspecified  
- Current worker is single-run and single-process; if needed, add lock files to prevent overlapping runs.

