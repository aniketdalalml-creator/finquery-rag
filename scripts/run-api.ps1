# Start FinQuery FastAPI (run in a separate terminal from Streamlit)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
}

$env:PYTHONPATH = "."
Write-Host "Starting API at http://localhost:8000" -ForegroundColor Green
Write-Host "Docs: http://localhost:8000/docs" -ForegroundColor Cyan
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
