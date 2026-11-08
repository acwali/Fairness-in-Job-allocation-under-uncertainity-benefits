# NSW versioned repository package

The folder NSW_Versioned_Repository contains the complete tracked project snapshot. The Git bundle next to it carries the version history. The two forms contain the same tracked project files.

## Open as a Git repository

Extract this ZIP. In PowerShell, change to the extracted folder and run:

```powershell
git clone -b main .\NSW_Versioned_Repository.bundle .\fair_Job_allocation_versioned
cd .\fair_Job_allocation_versioned
git log --oneline -2
```

The new folder is separate from your existing fair_Job_allocation project. Open it in VS Code. For a file-only copy, open the included NSW_Versioned_Repository folder.

## Verify or rerun

Read docs/reproducibility.md and data/README.md. The raw NSW files, virtual environment, and participant-level score tables are excluded. Acquire the original raw files locally, verify their checksums, then run the pipeline. Keep results/manifest.csv and results/logs/run_all.log with the aggregate results. The manifest identifies the source commit used for the included run.

The code-license choice, individual contribution statements, and compiled submission PDFs still require confirmation or completion. See docs/requirements_matrix.md for precise status.

