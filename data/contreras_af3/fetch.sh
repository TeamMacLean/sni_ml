#!/bin/bash
# Fetch all Contreras et al AF3 multimer archives from Zenodo 11546022.
# Resumable (curl -C -). Writes into zips/.
set -u
cd "$(dirname "$0")"
mkdir -p zips
BASE="https://zenodo.org/records/11546022/files"

# Priority order: NRC2 stoichiometry sweep first (gold dataset), then benchmarks,
# then broader CC-NLR panel.
FILES=(
  "NRC2_hexamers.zip"
  "NRC2_pentamers.zip"
  "NRC2_tetramers.zip"
  "NRC2_heptamers.zip"
  "NRC2_octamers.zip"
  "Benchmarks.zip"
  "AF_benchmark.zip"
  "CC.zip"
  "CCG10.zip"
  "CCR.zip"
)

for f in "${FILES[@]}"; do
  out="zips/$f"
  url="$BASE/$f"
  echo "=== $(date -u +%FT%TZ)  $f ==="
  curl -L --fail --retry 3 --retry-delay 5 -C - -o "$out" "$url" \
    && echo "  ok: $(ls -la "$out" | awk '{print $5}') bytes" \
    || echo "  FAILED: $f"
done
echo "=== done $(date -u +%FT%TZ) ==="
ls -la zips/
