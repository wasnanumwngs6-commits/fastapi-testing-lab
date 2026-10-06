# fastapi-testing-lab

A small Product API and the testing exercises from the FastAPI testing lab:
pytest unit tests, Postman API tests, a Postman integration flow, CSV-driven
tests, FastAPI `TestClient` integration tests, Newman, and GitHub Actions.

## Setup (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.

## Run the API

```powershell
uvicorn app.main:app --reload --port 8000
```

The API documentation is at <http://127.0.0.1:8000/docs>. Example credentials
for this exercise are `admin` / `admin123`.

## Run tests

```powershell
pytest tests/unit -v
pytest tests/integration -v
pytest --cov=app --cov-report=term-missing
```

The in-memory repository and token store are recreated by `create_app()`, so
each `TestClient` test starts with the seed products and a clean authentication
state.

## Postman and Newman

Import `postman/API-Testing-Lab.postman_collection.json` and
`postman/local.postman_environment.json` into Postman, select the **Local**
environment, and start the API on port 8000. The collection contains the
`01-Unit-API-Tests`, `02-Integration-Flow`, and `03-Data-Driven` folders.
Choose `postman/data/products.csv` as the data file when running the
data-driven folder.

Install Node.js 22 or newer, then install the Newman CLI and HTML reporter:

```powershell
npm install -g newman newman-reporter-htmlextra
python scripts/run_postman.py
```

The script starts and stops the API itself, runs the first two folders and the
CSV-driven folder, and writes the HTML report to `reports/postman-report.html`.
