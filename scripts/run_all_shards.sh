#!/bin/bash
# Drive the whole grid: every (questioner model, seed) shard, in sequence.
#
#   bash scripts/run_all_shards.sh results/grid_2026_09
#
# Models and seeds come from the environment so a run can be resumed or narrowed
# without editing this file:
#   MODELS="a b c" SEEDS="0 1 2" bash scripts/run_all_shards.sh <outdir>
#
# Completed shards are skipped, so re-running after a failure resumes rather than
# starting over. A failed shard does not stop the rest; the summary at the end
# lists what to retry.
set -u
OUT="${1:?usage: run_all_shards.sh <outdir>}"
MODELS="${MODELS:-Qwen/Qwen3.5-4B Qwen/Qwen3.6-27B Qwen/Qwen3.5-397B-A17B}"
SEEDS="${SEEDS:-0 1 2}"
HERE="$(dirname "$0")"

mkdir -p "$OUT"
failed=""
for model in $MODELS; do
  for seed in $SEEDS; do
    tag=$(echo "$model" | tr '/:' '__')_s$seed
    dir="$OUT/$tag"
    if [ -f "$dir/curve/round_curve.json" ] && [ -f "$dir/caps/round_cap_sweep.json" ]; then
      echo "skip $tag (already complete)"
      continue
    fi
    echo "=== $tag ==="
    if bash "$HERE/run_full_grid.sh" "$model" "$seed" "$dir"; then
      echo "ok $tag"
    else
      echo "FAILED $tag" >&2
      failed="$failed $tag"
    fi
  done
done

if [ -n "$failed" ]; then
  echo ""
  echo "shards that failed (re-run this script to retry only these):$failed" >&2
  exit 1
fi
echo ""
echo "all shards complete → $OUT"
echo "next: python scripts/analyze_grid.py --run $OUT"
