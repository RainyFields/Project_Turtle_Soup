#!/bin/bash
# Full E1+E2 grid, one shard = (questioner model, seed).
# Usage: run_full_grid.sh <model> <seed> <outdir>
# E1: round curve over the verified set, 30 checkpoint rounds, clue-only composite.
# E2: cap sweep {5..30}, composite with 397B logic rater (2 samples).
set -u
# Use the interpreter of the active environment; .venv is not guaranteed to exist.
PY="${PY:-$(command -v python3 || command -v python)}"
MODEL="$1"; SEED="$2"; OUT="$3"
cd "$(dirname "$0")/.."
# The verified set only (data/puzzles/real/). Derived at run time so the grid
# never silently picks up a generated puzzle, and never goes stale on renumber.
ORACLE_PROVIDER="${ORACLE_PROVIDER:-openrouter}"
ORACLE="${ORACLE_MODEL:-z-ai/glm-5.3-flash}"
if [ "$ORACLE_PROVIDER" = "tinker" ]; then
  echo "refusing to run: the Questioners are sampled through tinker, so a tinker" >&2
  echo "Oracle shares their family. Set ORACLE_PROVIDER/ORACLE_MODEL." >&2
  exit 2
fi

PUZZLES=$("$PY" -c "from engine.game import list_puzzle_ids; print(' '.join(list_puzzle_ids(family='real')))")
if [ -z "$PUZZLES" ]; then echo "no puzzles in data/puzzles/real/" >&2; exit 1; fi
echo "puzzles: $PUZZLES"
# The Oracle and the logic judge must come from a different model family than the
# Questioners. Sharing one makes "scale effect" and "resemblance to the Oracle"
# inseparable: a same-family question is easier for the Oracle to read, and that
# advantage does not reach the other models equally. Override per run.
export TINKER_THINK=0

"$PY" scripts/run_round_curve.py \
  --puzzles $PUZZLES --max-rounds 30 --seeds "$SEED" \
  --questioner-provider tinker --questioner-model "$MODEL" \
  --oracle-provider "$ORACLE_PROVIDER" --oracle-model "$ORACLE" \
  --judge composite \
  --output "$OUT/curve" > "$OUT/curve.log" 2>&1
E1=$?

"$PY" scripts/run_round_cap_sweep.py \
  --puzzles $PUZZLES --round-caps 5 10 15 20 25 30 --seeds "$SEED" \
  --questioner-provider tinker --questioner-model "$MODEL" \
  --oracle-provider "$ORACLE_PROVIDER" --oracle-model "$ORACLE" \
  --judge composite --judge-provider "$ORACLE_PROVIDER" --judge-model "$ORACLE" --logic-samples 2 \
  --output "$OUT/caps" > "$OUT/caps.log" 2>&1
E2=$?

echo "shard done model=$MODEL seed=$SEED e1=$E1 e2=$E2"
exit $(( E1 + E2 ))
