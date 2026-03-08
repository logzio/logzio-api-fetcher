# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python service that periodically fetches data from various APIs and ships logs to Logz.io. Runs as a Docker container with YAML-based configuration. Uses Pydantic for validation, `requests` for HTTP, and threading for concurrent API scraping.

## Commands

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run locally
```bash
python -m src.main --level DEBUG
```
Expects config at `./src/shared/config.yaml`.

### Run unit tests
```bash
PYTHONPATH=. pytest --cov-report term-missing --cov=src tests/UnitTests/test_*.py
```

### Run a single test file
```bash
PYTHONPATH=. pytest tests/UnitTests/test_cloudflare.py
```

### Run a single test
```bash
PYTHONPATH=. pytest tests/UnitTests/test_cloudflare.py::TestCloudflare::test_method_name
```

### Docker build and run
```bash
docker build -f dockerfile -t logzio/logzio-api-fetcher .
docker run --name logzio-api-fetcher -v "$(pwd)":/app/src/shared logzio/logzio-api-fetcher --level DEBUG
```

## Architecture

### Data Flow
1. **`src/main.py`** — Entry point. Parses CLI args (`--level`, `--config`), sets up logging.
2. **`src/config/ConfigReader.py`** — Reads YAML config, instantiates API fetcher and LogzioShipper objects using `API_TYPES_TO_CLASS_NAME_MAPPING` dict to resolve type strings to classes.
3. **`src/manager/TaskManager.py`** — Runs each API fetcher in its own thread on a configurable interval (`scrape_interval_minutes`). Handles graceful shutdown via signal handlers.
4. Each API's `send_request()` fetches data, handles pagination, then passes results to **`src/output/LogzioShipper.py`** which batches and ships logs to Logz.io.

### Adding a New API Type
1. Create a new class in `src/apis/<api_name>/` inheriting from `ApiFetcher` (or a more specific parent like `OAuthApi`).
2. Override `send_request()` if custom fetch logic is needed.
3. Register the type string → class name in `API_TYPES_TO_CLASS_NAME_MAPPING` in `ConfigReader.py`.
4. Import the class at the top of `ConfigReader.py` (classes are resolved via `globals()`).

### Key Base Class: `ApiFetcher` (`src/apis/general/Api.py`)
- Pydantic `BaseModel` with fields for url, headers, body, method, pagination, etc.
- Handles GET/POST requests, response data extraction via dot-notation path (`response_data_path`), pagination (URL/body/headers-based), and dynamic variable substitution from responses (`next_url`, `next_body` with `{res.field.path}` syntax).

### Pagination System (`src/apis/general/PaginationSettings.py`)
Three pagination types: `URL`, `BODY`, `HEADERS`. Stop conditions: `empty`, `equals`, `contains`. Configured per-API in YAML.

### Output: LogzioShipper (`src/output/LogzioShipper.py`)
Batches logs (max 1MB per batch, 500KB per log). Retries 3 times with backoff. Supports single output for all APIs or multiple outputs routed by API name.

### Logging
`MaskInfoFormatter` (`src/utils/MaskInfoFormatter.py`) automatically masks tokens/secrets in log output.

## Testing

- **Unit tests** in `tests/UnitTests/` — use `pytest` with `responses` library for HTTP mocking.
- **E2E tests** in `e2e_tests/` — require environment variables for API credentials and Logz.io tokens. Run via `python -m unittest`.
- **Test configs** in `tests/testConfigs/`.

## Configuration

YAML config has two top-level keys: `apis` (list of API configs with `type` field) and `logzio` (output config with `url` and `token`). See README.md for full field reference per API type.

## Python Version

Python 3.12 (as specified in Dockerfile and CI).
