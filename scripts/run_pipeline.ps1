# One-shot end-to-end pipeline for a solo run on Windows.
# Usage:  .\scripts\run_pipeline.ps1 [-N 100000] [-SkipInstall] [-SkipBench]
# Runs: Qdrant up -> install -> build-evalset -> ingest -> dense baseline (tag phase1-baseline)
#       -> hybrid eval -> benchmark (against a temporary API) -> report.
param(
    [int]$N = 100000,
    [switch]$SkipInstall,
    [switch]$SkipBench
)
$ErrorActionPreference = "Stop"
$py = (Get-Command python).Source

function Step([string]$msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }

function InGit { git rev-parse --is-inside-work-tree 2>$null | Out-Null; return $LASTEXITCODE -eq 0 }

Step "1/9  Qdrant up"
docker compose up -d

if (-not $SkipInstall) {
    Step "2/9  install dependencies"
    & $py -m pip install -r requirements.txt
    & $py -m pip install -e .
}

Step "3/9  build eval set (seed 42)"
& $py -m trustrag.cli build-evalset

Step "4/9  ingest $N passages"
& $py -m trustrag.cli ingest --n $N

Step "5/9  Phase 1 dense baseline"
& $py -m trustrag.cli eval --mode dense --split test --judge non-llm
if (InGit) {
    git add results data/eval
    git commit -m "chore: Phase 1 dense baseline results" --allow-empty
    git tag -f phase1-baseline
    Write-Host "tagged phase1-baseline" -ForegroundColor Green
}

Step "6/9  Phase 2 hybrid eval"
& $py -m trustrag.cli eval --mode hybrid --split test --judge non-llm

if (-not $SkipBench) {
    Step "7/9  start API (background)"
    $api = Start-Process -FilePath $py -ArgumentList @("-m","trustrag.cli","serve-api","--port","8000") -PassThru -WindowStyle Hidden
    $ready = $false
    for ($i = 0; $i -lt 90; $i++) {
        try { $null = Invoke-RestMethod "http://localhost:8000/health" -TimeoutSec 2; $ready = $true; break } catch { Start-Sleep 2 }
    }
    if (-not $ready) { Write-Warning "API did not become healthy; skipping benchmark"; }
    else {
        Step "8/9  latency benchmark (hybrid, 100 queries, cache off)"
        & $py -m trustrag.cli bench --mode hybrid --n 100 --no-cache
    }
    if ($api -and -not $api.HasExited) { Stop-Process -Id $api.Id -Force }
}

Step "9/9  benchmark report"
& $py -m trustrag.cli report
if (InGit) {
    git add results docs
    git commit -m "chore: Phase 2 hybrid results + benchmark report" --allow-empty
}

Write-Host "`nPipeline complete." -ForegroundColor Green
Write-Host "Tags:"; git tag --list
Write-Host "Next: add GROQ_API_KEY to .env, then re-run:"
Write-Host "  python -m trustrag.cli eval --mode hybrid --split test --judge llm"
Write-Host "  python -m trustrag.cli serve-api ; python -m trustrag.cli serve-ui"
