# FinQuery RAG — one-time setup (Windows PowerShell)
# Run from repo root:  .\scripts\setup.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "Creating virtual environment (.venv)..." -ForegroundColor Cyan
python -m venv .venv

Write-Host "Activating and installing dependencies..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example — add GROQ_API_KEY and JINA_API_KEY" -ForegroundColor Yellow
} else {
    Write-Host ".env already exists" -ForegroundColor Green
}

$env:PYTHONPATH = "."
python -m pytest tests -q

Write-Host ""
Write-Host "Setup complete. Next steps:" -ForegroundColor Green
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  `$env:PYTHONPATH = '.'"
Write-Host "  python src/pipeline.py          # ingest (needs API keys)"
Write-Host "  uvicorn api.main:app --reload --port 8000"
Write-Host "  streamlit run app/streamlit_app.py"
