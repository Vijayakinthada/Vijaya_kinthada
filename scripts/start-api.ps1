# Start Activity API (Windows)
# Prerequisites: Python 3.12+, Docker running for Postgres

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Write-Host "Starting PostgreSQL..."
Set-Location $root
docker compose up -d

Set-Location "$root\api"
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}
& .\.venv\Scripts\Activate.ps1

Write-Host "Installing dependencies..."
pip install -r requirements.txt -q

Write-Host "Running migrations..."
alembic upgrade head

Write-Host "Activity API -> http://localhost:8000/docs"
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
