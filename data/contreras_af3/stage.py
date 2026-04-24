#!/usr/bin/env python3
"""
Stage Contreras AF3 zip archives into a layout the SolNRCH resistosome pipeline
can ingest.

For each zip:
  - Extract only the top-ranked model (`*_model_0.cif`) and matching
    `*_summary_confidences_0.json` for each seed directory.
  - Drop __MACOSX/ AppleDouble cruft, drop `full_data_*.json` (170 MB each),
    drop the redundant top-level `model_0/` index directory, drop additional
    candidate models 1-4.
  - Rename the seed token from `_seed_random_<N>` to `_seed<N>` so the
    pipeline's `_seed(\\d+)` regex picks it up for replicate grouping.
  - Write to staging/<archive>/<protein>_seed<N>/{model.cif, summary_confidences.json}.

Inputs : zips/<name>.zip
Outputs: staging/<name>/...
"""
import os, re, sys, zipfile, shutil
from pathlib import Path

ZIPS = Path(__file__).parent / "zips"
OUT  = Path(__file__).parent / "staging"

# Top-level prefix (e.g. "hexamers/", "Benchmarks/", "CC/") is optional —
# NRC2_tetramers.zip puts fold_ dirs at archive root.
TOP = r"(?:[^/]+/)?"
SEED_RANDOM_DIR_RE = re.compile(rf"^{TOP}fold_(?P<base>.+?)_seed_random_(?P<seed>\d+)/")
# `_seed_<N>` without `random_` — used for seed 1 in the tetramer zip
SEED_PLAIN_DIR_RE  = re.compile(rf"^{TOP}fold_(?P<base>.+?)_seed_(?P<seed>\d+)/")
# Timestamp pattern: _YYYY_MM_DD_HH_MM — Contreras' default for the "seed 1" run
TIMESTAMP_DIR_RE   = re.compile(rf"^{TOP}fold_(?P<base>.+?)_\d{{4}}_\d{{2}}_\d{{2}}_\d{{2}}_\d{{2}}/")
MODEL0_RE   = re.compile(r"_model_0\.cif$")
CONF0_RE    = re.compile(r"_summary_confidences_0\.json$")

def is_cruft(member: str) -> bool:
    if "__MACOSX" in member: return True
    name = member.rsplit("/", 1)[-1]
    if name.startswith("._"): return True
    if "full_data" in name: return True
    return False

def stage_zip(zip_path: Path, out_root: Path):
    archive_name = zip_path.stem
    out_dir = out_root / archive_name
    out_dir.mkdir(parents=True, exist_ok=True)

    kept = 0
    skipped = 0
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            name = info.filename
            if info.is_dir():               continue
            if is_cruft(name):              skipped += 1; continue
            m = SEED_RANDOM_DIR_RE.match(name)
            if m:
                base = m.group("base")
                seed = int(m.group("seed"))
            elif (m := SEED_PLAIN_DIR_RE.match(name)):
                base = m.group("base")
                seed = int(m.group("seed"))
            elif (m := TIMESTAMP_DIR_RE.match(name)):
                base = m.group("base")
                seed = 1  # Contreras manifest convention: timestamp dir = seed 1
            else:
                skipped += 1; continue
            tail = name[m.end():]
            if "/" in tail:                 skipped += 1; continue   # nested
            if MODEL0_RE.search(tail):
                ext = "model.cif"
            elif CONF0_RE.search(tail):
                ext = "summary_confidences.json"
            else:
                skipped += 1; continue
            target_dir = out_dir / f"{base}_seed{seed}"
            target_dir.mkdir(parents=True, exist_ok=True)
            # canonical names the pipeline expects
            target_path = target_dir / f"{base}_seed{seed}_{ext}"
            with zf.open(info) as src, open(target_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            kept += 1

    return kept, skipped

def main():
    zips = sorted(ZIPS.glob("*.zip"))
    if len(sys.argv) > 1:
        wanted = set(sys.argv[1:])
        zips = [z for z in zips if z.name in wanted or z.stem in wanted]
    OUT.mkdir(parents=True, exist_ok=True)
    total_kept = total_skipped = 0
    for z in zips:
        size_gb = z.stat().st_size / 2**30
        print(f"[{z.name}] {size_gb:.2f} GB", flush=True)
        k, s = stage_zip(z, OUT)
        total_kept += k; total_skipped += s
        print(f"   kept {k}, skipped {s}", flush=True)
    print(f"=== TOTAL kept {total_kept}, skipped {total_skipped} ===")

if __name__ == "__main__":
    main()
