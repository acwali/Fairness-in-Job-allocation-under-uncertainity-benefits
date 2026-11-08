import argparse
import csv
from datetime import datetime, timezone
from hashlib import file_digest
import json
from pathlib import Path
import subprocess
import sys


CONFIG = Path("configs/frozen_run.json")
LOCK = Path("requirements-lock.txt")
MANIFEST = Path("results/manifest.csv")
SOURCE_PATHS = ("*.py", "run_all.ps1", CONFIG.as_posix(), LOCK.as_posix())


def sha256(path):
    with Path(path).open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def verify_inputs(config):
    for name, expected in config["data"]["inputs"].items():
        actual = sha256(name)
        if actual != expected:
            raise ValueError(f"Input checksum mismatch: {name}\nExpected {expected}\nActual   {actual}")


def git(*args):
    try:
        return subprocess.run(
            ("git", *args), capture_output=True, text=True, check=True
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""


def clean_source_commit():
    if git("rev-parse", "--show-prefix") or git("rev-parse", "--is-inside-work-tree") != "true":
        return ""
    commit = git("rev-parse", "HEAD")
    if not commit:
        return ""
    expected = {path.name for path in Path(".").glob("*.py")}
    expected.update(SOURCE_PATHS[1:])
    tracked = set(git("ls-files", "--", *SOURCE_PATHS).splitlines())
    if not expected <= tracked:
        return ""
    status = git("status", "--porcelain", "--untracked-files=all", "--", *SOURCE_PATHS)
    return "" if status else commit


def output_specs():
    prefix = "results/metrics/"
    groups = {
        "experiment1_ate.py": ["ate_estimators.csv"],
        "verify_inference.py": ["inference_checks.csv"],
        "experiment2_predictive_baselines.py": ["predictive_baselines.csv", "predictive_baselines_paired.csv"],
        "experiment2_baselines.py": ["baseline_policy_values.csv"],
        "experiment2_group_audit.py": ["policy_fairness_summary.csv", "policy_group_metrics.csv"],
        "experiment3_constraints.py": ["constraint_outer_summary.csv", "constraint_selections.csv", "constraint_validation_candidates.csv"],
        "experiment3_comparison.py": ["constraint_matched_utility_audit.csv", "constraint_paired_20pct.csv"],
        "experiment3_fairness_utility.py": ["fairness_utility_frontier.csv", "fairness_utility_matched_summary.csv", "nsw_subgroup_ess.csv"],
        "experiment4_simulation.py": ["simulation_runs.csv", "simulation_summary.csv"],
        "experiment5_overlap.py": ["overlap_simulation_runs.csv", "overlap_simulation_summary.csv"],
        "experiment6_refitting.py": ["refitting/" + name for name in ("refitting_fold_runs.csv", "refitting_replicates.csv", "refitting_summary.csv")],
        "experiment7_outcome_fairness.py": ["outcome_fairness_coverage.csv", "outcome_fairness_groups.csv", "outcome_fairness_summary.csv"],
        "experiment8_calibration.py": ["predictive_calibration_bins.csv", "predictive_calibration_groups.csv", "predictive_calibration_summary.csv"],
    }
    for script, names in groups.items():
        for name in names:
            yield prefix + name, "python " + script
    for directory, extra in (("asinh_on_asinh", ""), ("asinh_on_raw", " --evaluation-scores results/experiment2")):
        for name in groups["experiment3_constraints.py"]:
            yield (
                f"{prefix}{directory}/{name}",
                f"python experiment3_constraints.py --selection-scores results/experiment2_asinh{extra} --output {prefix}{directory}",
            )
    for figure, script, formats in (
        ("nsw_main_results", "make_nsw_results_figure.py", ("pdf", "png")),
        ("fairness_utility_frontier_40pct", "experiment3_fairness_utility.py", ("pdf", "png")),
        ("nsw_causal_dag", "draw_nsw_causal_dag.py", ("svg", "png")),
    ):
        for extension in formats:
            yield f"results/figures/{figure}.{extension}", "python " + script


def write_manifest(config, commit):
    if commit and clean_source_commit() != commit:
        raise ValueError("Tracked analysis sources changed during the run.")
    run = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = json.dumps(config["data"]["inputs"], sort_keys=True)
    config_hash = sha256(CONFIG)
    lock_hash = sha256(LOCK)
    rows = []
    for path, command in output_specs():
        rows.append({
            "artifact_path": path,
            "command": command,
            "config_path": CONFIG.as_posix(),
            "config_sha256": config_hash,
            "environment_lock_sha256": lock_hash,
            "dataset_version": config["data"]["name"],
            "run_input_sha256": inputs,
            "code_commit": commit,
            "python_version": sys.version.split()[0],
            "run_completed_utc": run,
            "execution_status": "completed_versioned" if commit else "completed_commit_unverified",
            "artifact_sha256": sha256(path),
        })
    temporary = MANIFEST.with_suffix(".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(MANIFEST)
    print(f"Wrote {len(rows)} artifact records to {MANIFEST}")


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verify-inputs", action="store_true")
    mode.add_argument("--source-commit", action="store_true")
    mode.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--code-commit", default="")
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    verify_inputs(config)
    if args.source_commit:
        print(clean_source_commit())
    elif args.write_manifest:
        write_manifest(config, args.code_commit)
    else:
        print("Verified both original NSW input checksums.")


if __name__ == "__main__":
    main()
