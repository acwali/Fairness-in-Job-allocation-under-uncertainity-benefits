# Repository and reproducibility

This repository snapshot was prepared from the local NSW project. The first commit pins the source, configuration record, and dependency lock used for the isolated rerun. The second commit records the resulting aggregate outputs and manifest. The manifest points to the first, experiment-producing commit. It does not attribute older runs to that commit.

## Run on Windows

1. Open the repository folder in PowerShell. Use Python 3.14 and Git.
2. Run `python -m venv .venv`, then ` .\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt`.
3. Follow [data/README.md](../data/README.md) to acquire and verify the two local inputs.
4. Run `& .\run_all.ps1`. It verifies input hashes and regenerates the analysis, figure, and manifest. Keep the source, configuration, and lock clean and tracked if you want Git provenance recorded.
5. For a quick inference-only smoke check, run ` .\.venv\Scripts\python.exe verify_inference.py`. It checks the synthetic inference fixture only. Use the full run for NSW policy results.

[configs/frozen_run.json](../configs/frozen_run.json) records the settings read from the implementation. The executable parameter definitions live in the scripts. When changing one, update the config record in the same commit. Input hashes are enforced by the runner. The manifest records input, dependency, config, and artifact hashes, as well as the source revision when verified. Results may differ byte-for-byte across dependency or platform versions.

## Licensing and submission

The authors' choice of a code license is pending. Confirm which license both authors or the institution authorize before adding a LICENSE file or publishing the repository. Source data have a separate provenance and reuse record in [data/README.md](../data/README.md) and [data_card.md](data_card.md). The raw NSW input files and participant-level scores are excluded from Git and from the submission package.

See [requirements_matrix.md](requirements_matrix.md) for the itemized evidence and outstanding submission items.
