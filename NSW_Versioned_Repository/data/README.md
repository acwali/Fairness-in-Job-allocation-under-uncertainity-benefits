# Acquire and verify the NSW inputs

Use the Dehejia–Wahba experimental RE74 subset. The two original text files have 185 treated and 260 experimental control participants. See [the dataset documentation](https://users.nber.org/~rdehejia/data/.nswdata2.html) and the [data card](../docs/data_card.md) for the schema, subgroup definitions, sample restrictions, and reuse notes. The verification record uses the original bytes, including their line endings.

From the repository root in PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path .\data\raw | Out-Null
$base = 'https://users.nber.org/~rdehejia/data'
foreach ($file in @('nswre74_treated.txt', 'nswre74_control.txt')) {
    $target = Join-Path '.\data\raw' $file
    if (-not (Test-Path -LiteralPath $target)) {
        Invoke-WebRequest -Uri "$base/$file" -OutFile $target
    }
}
.\.venv\Scripts\python.exe .\provenance.py --verify-inputs
```

Download the named files manually from the source directory if the command cannot reach it. Compare these hashes before proceeding.

| Input | SHA-256 |
|---|---|
| `nswre74_treated.txt` | `e7b742fe0ff07a0f45e129b4ff108bb9611cd83d53604732c48a8a0a3e20eda3` |
| `nswre74_control.txt` | `a1364cea459d953dc691a667d99194b4ad335d6d550354fe23a5d2dc58d729b5` |

The 445 rows loaded from these files are the empirical sample. The loader checks file shape, treatment indicators, and finite values. The project indexes each participant by row order and uses RE78 as the earnings outcome. The observational overlap scenarios are synthetic. Store input files and participant-level scores locally. The repository includes only code, documented provenance, and aggregate or simulated results.
