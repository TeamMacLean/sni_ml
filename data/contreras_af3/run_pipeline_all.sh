#!/bin/bash
# Run resistosome_pipeline against every Contreras archive subdir.
# Output: results/004_full_run/<archive>/
set -u
ROOT="/Users/macleand/Desktop/sni_paper"
PIPE="$ROOT/SolNRCH_foldome/resistosome_pipeline/run_pipeline.py"
HMM="$ROOT/SolNRCH_foldome/structural_analysis/main/MADA.hmm"
MHD="$ROOT/SolNRCH_foldome/structural_analysis/main/NRCH_MHD_nlrexp_coords.csv"
PLOOP="$ROOT/SolNRCH_foldome/structural_analysis/main/NRCH_ploop_nlrexp_coords.csv"
NBARC="$ROOT/SolNRCH_foldome/structural_analysis/main/NRCH_clade_filtered_len_NBARC_filtered_95_coords.csv"
STAGING="$ROOT/sni_ml/data/contreras_af3/staging"
OUT="$ROOT/sni_ml/results/004_full_run"

# The pipeline shells out to `hmmsearch` and `mkdssp` via PATH lookup
# (subprocess.run(['hmmsearch', ...])). Invoking python by absolute path
# does NOT put the env's bin/ on PATH, so we prepend it explicitly.
ENV_BIN="/Users/macleand/mamba/envs/sni-pipeline/bin"
export PATH="$ENV_BIN:$PATH"
PY="$ENV_BIN/python"

# Sanity-check the external tools are actually visible before doing any work
for tool in hmmsearch mkdssp; do
  if ! command -v "$tool" >/dev/null; then
    echo "FATAL: $tool not on PATH after activation. Aborting." >&2; exit 2
  fi
  echo "  $tool -> $(command -v $tool)"
done

for arc in AF_benchmark Benchmarks CC CCG10 CCR NRC2_tetramers NRC2_pentamers NRC2_hexamers NRC2_heptamers NRC2_octamers; do
  in="$STAGING/$arc"
  out="$OUT/$arc"
  mkdir -p "$out"
  echo "=== $(date -u +%FT%TZ)  $arc ($(ls "$in" | wc -l | tr -d ' ') protein-seed dirs) ==="
  "$PY" "$PIPE" \
      --input_dir "$in" \
      --output_dir "$out" \
      --mhd_csv "$MHD" \
      --ploop_csv "$PLOOP" \
      --nbarc_csv "$NBARC" \
      --hmm "$HMM" \
      --hmm_fallback_dssp \
      --workers 8 \
      --log_level WARNING \
    > "$out/run.log" 2>&1
  echo "   exit=$?  $(ls "$out"/*.xlsx 2>/dev/null | wc -l | tr -d ' ') xlsx"
done
echo "=== done $(date -u +%FT%TZ) ==="
