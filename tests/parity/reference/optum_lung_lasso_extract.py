"""Extract the Optum EHR LASSO model from the OHDSI study package.

The fitted model is distributed as a `plpModel` directory inside
`ohdsi-studies/lungCancerPrognostic` (Apache-2.0, declared at line 43 of the
package DESCRIPTION, there is no root LICENSE file, so GitHub reports the
repository as unlicensed). Four of the six files in that directory matter:

    model.json              the betas PatientLevelPrediction actually scores
                            with, rounded to 4 decimal places by the JSON writer
    covariateImportance.csv the same betas UNROUNDED, plus a human-readable
                            covariateName, analysisId and conceptId for each
    preprocessing.json      normFactors (the divisor applied to every covariate
                            at predict time) and the deleted-covariate lists
    trainDetails.json       development database and attrition

Nothing here is retyped. The script asserts the two coefficient files agree,
`round(covariateImportance, 4) == model.json` for all 278 non-zero covariates,
which is a genuine cross-check, because the two are written by different code
paths in PatientLevelPrediction::savePlpModel.

Run:

    python tests/parity/reference/optum_lung_lasso_extract.py [--repo DIR]

With no --repo it clones the pinned commit into a temporary directory. It
rewrites src/cancerverse_baseline/lung/detection/data/optum_lung_lasso_2023.json in
place and prints a summary.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "https://github.com/ohdsi-studies/lungCancerPrognostic"
COMMIT = "61c526eaba3f3130b2ba3a45c5f46759fcf4994c"  # master, 2022-10-03

#: sha256 of each file as read on 2026-08-14. The model directory has not
#: changed since the 2022 commit above; if one of these moves, the coefficients
#: moved and this script should not silently rewrite the package data.
DIGESTS = {
    "model.json":
        "7661a67ac77d8b1aa49b0ece0d027a3548c3b67e2e55a688329d1f7237f6a282",
    "covariateImportance.csv":
        "f33c3adb48bedbd7f20c7c72ae3a28c6299f0bfd01a63eb02f8c4b464c4e5e5c",
    "preprocessing.json":
        "be457311b8087a00be7382ee73e4aa5e131f80127060f74cd8fc16025e1b28a6",
    "trainDetails.json":
        "c8aeb8485f68816bc57fd246ee98c41143884e9a62c64c6c73692e538c3d26f8",
}

OUT = (Path(__file__).resolve().parents[3] / "src" / "cancerverse_baseline" / "lung"
       / "detection" / "data" / "optum_lung_lasso_2023.json")


def _clone(dest: Path) -> Path:
    subprocess.run(["git", "clone", "--quiet", REPO, str(dest)], check=True)
    subprocess.run(["git", "-C", str(dest), "checkout", "--quiet", COMMIT],
                   check=True)
    return dest


def extract(repo: Path) -> dict:
    d = repo / "inst" / "models" / "full_model"
    for name, want in DIGESTS.items():
        got = hashlib.sha256((d / name).read_bytes()).hexdigest()
        if got != want:
            raise SystemExit(f"{name}: sha256 {got}, expected {want}")

    model = json.loads((d / "model.json").read_text())
    ids = model["coefficients"]["covariateIds"]
    betas = model["coefficients"]["betas"]
    if len(ids) != len(betas):
        raise SystemExit("model.json: covariateIds and betas differ in length")

    pairs = list(zip(ids, betas, strict=True))
    intercept = next(b for i, b in pairs if i == "(Intercept)")
    nonzero = {int(i): b for i, b in pairs
               if i != "(Intercept)" and b != 0}

    # covariateImportance.csv carries a latin-1 degree sign in one lab name.
    meta = {int(r["covariateId"]): r for r in
            csv.DictReader((d / "covariateImportance.csv")
                           .open(encoding="latin-1"))}

    tidy = json.loads((d / "preprocessing.json").read_text())["tidyCovariates"]
    norm = dict(zip(tidy["normFactors"]["covariateId"],
                    tidy["normFactors"]["maxValue"], strict=True))

    coefficients = []
    for cid, beta in sorted(nonzero.items(), key=lambda kv: -abs(kv[1])):
        row = meta[cid]
        unrounded = float(row["covariateValue"])
        if round(unrounded, 4) != beta:
            raise SystemExit(
                f"{cid}: model.json says {beta}, covariateImportance.csv says "
                f"{unrounded} (rounds to {round(unrounded, 4)})")
        analysis_id = int(row["analysisId"])
        concept_id = int(row["conceptId"])
        # covariateId = conceptId * 1000 + analysisId, except for the analyses
        # that index a bucket rather than a concept (age group, smoking status),
        # which record conceptId 0.
        if cid % 1000 != analysis_id:
            raise SystemExit(f"{cid}: analysisId {analysis_id} does not decode")
        if concept_id and cid // 1000 != concept_id:
            raise SystemExit(f"{cid}: conceptId {concept_id} does not decode")
        if norm[cid] != 1:
            raise SystemExit(
                f"{cid}: normalisation factor {norm[cid]} is not 1; the module "
                "assumes every model covariate is a 0/1 indicator")
        coefficients.append({
            "covariate_id": cid,
            "beta": beta,
            "beta_unrounded": unrounded,
            "analysis_id": analysis_id,
            "concept_id": concept_id,
            "name": row["covariateName"],
        })

    train = json.loads((d / "trainDetails.json").read_text())
    attrition = train["attrition"]

    return {
        "model_id": "optum_lung_lasso",
        "source": {
            "repo": REPO,
            "commit": COMMIT,
            "path": "inst/models/full_model",
            "license": "Apache-2.0 (DESCRIPTION line 43; no root LICENSE file)",
            "extracted_by": "tests/parity/reference/optum_lung_lasso_extract.py",
            "sha256": DIGESTS,
        },
        "development_database": train["developmentDatabase"],
        "training_date": train["trainingDate"],
        "n_patients": attrition["targetCount"][-1],
        "n_outcomes": attrition["outcomes"][-1],
        "prior_variance": model["priorVariance"],
        "log_likelihood": model["log_likelihood"],
        "n_candidate_covariates": len(ids) - 1,
        "n_removed_infrequent": len(tidy["deletedInfrequentCovariateIds"]),
        "n_removed_redundant": len(tidy["deletedRedundantCovariateIds"]),
        "removed_redundant": sorted(tidy["deletedRedundantCovariateIds"]),
        "intercept": intercept,
        "coefficients": coefficients,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, help="existing clone of the study package")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)

    if args.repo:
        data = extract(args.repo)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            data = extract(_clone(Path(tmp) / "lungCancerPrognostic"))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=1) + "\n")
    print(f"wrote {args.out}")
    print(f"  intercept                {data['intercept']}")
    print(f"  non-zero coefficients    {len(data['coefficients'])}")
    print(f"  candidate covariates     {data['n_candidate_covariates']}")
    print(f"  development database     {data['development_database']}")
    print(f"  patients                 {data['n_patients']:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
