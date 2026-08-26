#!/bin/bash
# Full E1+E2 grid, one shard = (questioner model, seed).
# Usage: run_full_grid.sh <model> <seed> <outdir>
# E1: round curve, 11 puzzles, 30 checkpoint rounds, clue-only composite.
# E2: cap sweep {5..30}, composite with 397B logic rater (2 samples).
set -u
MODEL="$1"; SEED="$2"; OUT="$3"
cd "$(dirname "$0")/.."
PUZZLES="turtle_001 turtle_002 turtle_003 turtle_004 turtle_005 turtle_010 turtle_011 turtle_012 turtle_013 turtle_014 turtle_015"
ORACLE="Qwen/Qwen3.5-397B-A17B"
export TINKER_THINK=0

.venv/bin/python scripts/run_round_curve.py \
  --puzzles $PUZZLES --max-rounds 30 --seeds "$SEED" \
  --questioner-provider tinker --questioner-model "$MODEL" \
  --oracle-provider tinker --oracle-model "$ORACLE" \
  --judge composite \
  --output "$OUT/curve" > "$OUT/curve.log" 2>&1
E1=$?

.venv/bin/python scripts/run_round_cap_sweep.py \
  --puzzles $PUZZLES --round-caps 5 10 15 20 25 30 --seeds "$SEED" \
  --questioner-provider tinker --questioner-model "$MODEL" \
  --oracle-provider tinker --oracle-model "$ORACLE" \
  --judge composite --judge-provider tinker --judge-model "$ORACLE" --logic-samples 2 \
  --output "$OUT/caps" > "$OUT/caps.log" 2>&1
E2=$?

echo "shard done model=$MODEL seed=$SEED e1=$E1 e2=$E2"
exit $(( E1 + E2 ))
