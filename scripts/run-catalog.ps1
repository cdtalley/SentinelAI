# SentinelAI — start API + Postgres for catalog / Upwork demos (Windows)
# Usage: .\scripts\run-catalog.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

Write-Host "Starting Postgres + API..." -ForegroundColor Cyan
docker compose up -d --build postgres api

Write-Host ""
Write-Host "  API docs:  http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  Next.js:   cd frontend; npm install; npm run dev:catalog" -ForegroundColor Yellow
Write-Host "  Console:   http://localhost:3010/dashboard" -ForegroundColor Green
Write-Host ""
Write-Host "Full stack with Next in Docker: docker compose up -d --build" -ForegroundColor DarkGray
