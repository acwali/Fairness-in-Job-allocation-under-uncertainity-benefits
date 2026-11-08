param([string]$PythonExecutable = "")

$ErrorActionPreference = "Stop"

Push-Location -LiteralPath $PSScriptRoot
try {
    $python = if ($PythonExecutable) { $PythonExecutable } else { Join-Path $PSScriptRoot ".venv\Scripts\python.exe" }

    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
        throw "Missing .venv\Scripts\python.exe. Create the virtual environment first."
    }

    foreach ($dataFile in @(
        "data\raw\nswre74_treated.txt",
        "data\raw\nswre74_control.txt"
    )) {
        if (-not (Test-Path -LiteralPath $dataFile -PathType Leaf)) {
            throw "Missing NSW input file $dataFile"
        }
    }

    function Invoke-ProjectPython {
        Write-Host "`nRunning $($args -join ' ')" -ForegroundColor Cyan
        & $python @args
        if ($LASTEXITCODE -ne 0) {
            throw "Python step failed with exit code ${LASTEXITCODE}: $($args -join ' ')"
        }
    }

    $codeCommit = & $python provenance.py --source-commit
    if ($LASTEXITCODE -ne 0) { throw "Input or provenance check failed." }

    Invoke-ProjectPython check_data.py
    Invoke-ProjectPython experiment1_ate.py
    Invoke-ProjectPython verify_inference.py
    Invoke-ProjectPython experiment2_scores.py
    Invoke-ProjectPython experiment2_predictive_baselines.py
    Invoke-ProjectPython experiment2_baselines.py
    Invoke-ProjectPython experiment2_group_audit.py
    Invoke-ProjectPython experiment3_constraints.py
    Invoke-ProjectPython experiment3_comparison.py
    Invoke-ProjectPython experiment3_fairness_utility.py
    Invoke-ProjectPython experiment4_simulation.py
    Invoke-ProjectPython experiment5_overlap.py

    Invoke-ProjectPython experiment2_scores.py `
        --outcome asinh `
        --output results\experiment2_asinh

    Invoke-ProjectPython experiment3_constraints.py `
        --selection-scores results\experiment2_asinh `
        --output results\metrics\asinh_on_asinh

    Invoke-ProjectPython experiment3_constraints.py `
        --selection-scores results\experiment2_asinh `
        --evaluation-scores results\experiment2 `
        --output results\metrics\asinh_on_raw

    $transformedHash = (Get-FileHash -Algorithm SHA256 -LiteralPath `
        "results\metrics\asinh_on_asinh\constraint_selections.csv").Hash
    $rawHash = (Get-FileHash -Algorithm SHA256 -LiteralPath `
        "results\metrics\asinh_on_raw\constraint_selections.csv").Hash

    if ($transformedHash -ne $rawHash) {
        throw "The two evaluations selected different transformed-trained rules."
    }
    Write-Host "Verified identical transformed-policy selections."

    Invoke-ProjectPython experiment6_refitting.py
    Invoke-ProjectPython experiment7_outcome_fairness.py
    Invoke-ProjectPython experiment8_calibration.py
    Invoke-ProjectPython make_nsw_results_figure.py
    Invoke-ProjectPython draw_nsw_causal_dag.py
    Invoke-ProjectPython provenance.py --write-manifest "--code-commit=$codeCommit"

    Write-Host "`nFull run completed. See results\metrics and results\figures." `
        -ForegroundColor Green
}
finally {
    Pop-Location
}
