# AI Virtual Hospital (AI-VH) PowerShell Test Runner
# Mirrors Makefile targets for Windows environments

param (
    [Parameter(Position=0)]
    [ValidateSet("lint", "typecheck", "test-unit", "test-integration", "test-regression", "eval", "test-all", "up", "down")]
    [string]$Target = "test-all"
)

$ErrorActionPreference = "Stop"

switch ($Target) {
    "lint" {
        Write-Host "Running Secret Scanner..." -ForegroundColor Cyan
        py -3.13 scripts/scan_secrets.py
    }
    "typecheck" {
        Write-Host "Running Mypy Type Checker..." -ForegroundColor Cyan
        py -3.13 -m mypy src/vh
    }
    "test-unit" {
        Write-Host "Running Unit Tests..." -ForegroundColor Cyan
        py -3.13 -m pytest -m unit
    }
    "test-integration" {
        Write-Host "Running Integration Tests..." -ForegroundColor Cyan
        py -3.13 -m pytest -m integration
    }
    "test-regression" {
        Write-Host "Running Regression Tests..." -ForegroundColor Cyan
        py -3.13 -m pytest -m regression
    }
    "eval" {
        Write-Host "Running Evaluation Tests..." -ForegroundColor Cyan
        py -3.13 -m pytest -m eval
    }
    "test-all" {
        Write-Host "Running Secret Scanner..." -ForegroundColor Cyan
        py -3.13 scripts/scan_secrets.py
        Write-Host "Running Full Pytest Suite..." -ForegroundColor Cyan
        py -3.13 -m pytest
        Write-Host "All Verification Checks Passed!" -ForegroundColor Green
    }
    "up" {
        Write-Host "Starting Docker Compose services..." -ForegroundColor Cyan
        docker compose up -d
    }
    "down" {
        Write-Host "Stopping Docker Compose services..." -ForegroundColor Cyan
        docker compose down
    }
}
