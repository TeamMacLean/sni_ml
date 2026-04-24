#!/usr/bin/env python3
"""
Concatenate per-archive resistosome_analysis_summary.csv outputs into a single
feature matrix, parse predicted oligomer + protein from `ID`, join to
known_oligomer_states.csv ground truth, and write:
  results/004_full_run/feature_matrix.csv
  results/004_full_run/feature_matrix.xlsx

Each row = (archive, protein, predicted_oligomer) aggregate over seeds in that
archive. NRC2_<X>mers archives carry N_replicates=10; everything else 1.
"""
import re
from pathlib import Path
import pandas as pd

ROOT = Path("/Users/macleand/Desktop/sni_paper")
RUN  = ROOT / "sni_ml/results/004_full_run"
GT   = ROOT / "sni_ml/data/known_oligomer_states.csv"
OUT_CSV = RUN / "feature_matrix.csv"
OUT_XLSX = RUN / "feature_matrix.xlsx"

ARCHIVES = ["AF_benchmark", "Benchmarks", "CC", "CCG10", "CCR",
            "NRC2_tetramers", "NRC2_pentamers", "NRC2_hexamers",
            "NRC2_heptamers", "NRC2_octamers"]

OLIG_TOKEN = {"tetra": 4, "penta": 5, "hexa": 6, "hepta": 7, "octa": 8}
TOKEN_RE = re.compile(r"_(tetra|penta|hexa|hepta|octa)_")

STRIP_RE = re.compile(r"_(ccnbarc|tetra|penta|hexa|hepta|octa|oleic)")
def parse_id(idstr: str):
    """Return (protein_lower, predicted_oligomer_int)."""
    m = TOKEN_RE.search(idstr)
    olig = OLIG_TOKEN[m.group(1)] if m else 6   # Contreras default
    # Strip every known suffix segment to recover the bare protein name
    protein = STRIP_RE.sub("", idstr).strip("_").lower()
    return protein, olig

def main():
    parts = []
    for arc in ARCHIVES:
        csv = RUN / arc / "resistosome_analysis_summary.csv"
        if not csv.exists():
            print(f"  SKIP {arc} (no csv)"); continue
        df = pd.read_csv(csv)
        df.insert(0, "archive", arc)
        parts.append(df)
    full = pd.concat(parts, ignore_index=True)
    print(f"Pipeline rows (pre-parse): {len(full)}")

    parsed = full["ID"].apply(parse_id)
    full["protein"]            = [p[0] for p in parsed]
    full["predicted_oligomer"] = [p[1] for p in parsed]

    gt = pd.read_csv(GT)
    gt["protein"] = gt["ID"].str.lower()
    gt_cols = ["protein", "known_state", "evidence_tier", "functional_call",
               "source_pmid", "source_pdb", "in_current_18", "usable_for_analysis"]
    full = full.merge(gt[gt_cols], on="protein", how="left")

    # ground-truth oligomer as int when interpretable
    OLIG_NAME = {"tetramer":4, "pentamer":5, "hexamer":6, "heptamer":7,
                 "octamer":8, "octamer_plus":8}
    full["gt_oligomer"] = full["known_state"].map(OLIG_NAME)
    full["call_correct"] = pd.Series(
        [pd.NA if pd.isna(g) else (p == int(g))
         for p, g in zip(full["predicted_oligomer"], full["gt_oligomer"])],
        dtype="boolean")

    # Triple-deposit flag: nbnrc2a hexamer seed1 appears in AF_benchmark,
    # Benchmarks AND NRC2_hexamers (seed1 is one of 10 there)
    full["is_triple_deposit"] = (
        (full["protein"] == "nbnrc2a") &
        (full["predicted_oligomer"] == 6) &
        (full["archive"].isin(["AF_benchmark", "Benchmarks", "NRC2_hexamers"]))
    )

    # canonical column order: provenance + identity + GT + 11 SNI features + everything else
    SNI = ["ipTM_LCB", "Sum_CONTACTS", "BSA_INT_PROTO", "SD_THETA_ROT",
           "S_PROTO", "D_APEX", "THETA_APEX_mean", "L_APEX_mean",
           "H_ABS_mean", "MU_H_mean", "D_MHD_P_mean"]
    front = ["archive", "ID", "protein", "predicted_oligomer", "N_replicates",
             "N_chains", "Seeds",
             "known_state", "gt_oligomer", "evidence_tier", "functional_call",
             "in_current_18", "usable_for_analysis", "is_triple_deposit",
             "call_correct"]
    rest = [c for c in full.columns if c not in front + SNI]
    full = full[front + SNI + rest]

    full.to_csv(OUT_CSV, index=False)
    full.to_excel(OUT_XLSX, index=False)
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_XLSX}")
    print()
    print("=== ARCHIVE × PROTEIN COUNTS ===")
    print(full.groupby(["archive", "protein", "predicted_oligomer"]).size()
          .to_string())
    print()
    print("=== GT JOIN STATUS ===")
    print(f"  rows with GT: {full['gt_oligomer'].notna().sum()}")
    print(f"  rows w/o  GT: {full['gt_oligomer'].isna().sum()}")
    print()
    print("=== CALL CORRECT (rows with GT) ===")
    print(full[full['gt_oligomer'].notna()]
          .groupby(['archive','protein','predicted_oligomer','gt_oligomer'])
          ['call_correct'].first().to_string())

if __name__ == "__main__":
    main()
