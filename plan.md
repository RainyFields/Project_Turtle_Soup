# Evaluation Plan — Round-Curve & Round-Cap Studies

**Project**: `turtle-soup-bench`  
**Date**: 2026-06-11  
**Status**: Pilot implemented (`scripts/run_pilot.py`); full study not yet run  
**Dataset**: 11 puzzles — `turtle_001`–`005` (MVP) + `turtle_010`–`015` (generator pipeline, reviewed)

---

## Goals

Two complementary studies on **Questioner** performance. **Oracle is held fixed** across all runs so differences reflect question-asking / reasoning quality only.

| Study | Question | X-axis | Y-axis |
|-------|----------|--------|--------|
| **Exp 1 — Learning curve** | Does accuracy improve as the dialogue grows (no rush)? | Round \(r = 1 \ldots 30\) | Mean final-answer accuracy at round \(r\) |
| **Exp 2 — Round budget** | How well does the agent do under a hard turn limit? | Max rounds \(\in \{5,10,15,20,25,30\}\) | Mean accuracy when the game ends at that cap |

---

## Shared experimental setup

### Roles

| Role | Model (fixed) | Provider | Notes |
|------|---------------|----------|-------|
| **Oracle** | `gpt-4o` | openai | Same Oracle for all Questioner models |
| **Judge** | `gpt-4o` | openai | LLM-as-judge (`evaluation/judge.py`); fallback heuristic only on API failure |
| **Questioner** | see below | varies | Only variable under comparison |

### Questioner models (3 open-source reasoning)

Prioritize models with strong reasoning that are reproducible via existing or near-term providers:

| # | Model | Provider | API / deploy |
|---|-------|----------|--------------|
| 1 | **DeepSeek-R1** (`deepseek-reasoner`) | `deepseek` | `DEEPSEEK_API_KEY` |
| 2 | **QwQ-32B** (`qwq-32b`) | `qwen` | `QWEN_API_KEY` (DashScope OpenAI-compatible) |
| 3 | **Llama 3.3 70B** (`llama3.3:70b`) | `ollama` | Local `OLLAMA_BASE_URL` |

> If Ollama 70B is unavailable on hardware, fallback: `qwen2.5-72b-instruct` (Qwen) or `mistral-small` — document substitution in `results/<run_id>/config.json`.

### Puzzles & replication

- **Puzzles**: all 11 ids (`--puzzles all`)
- **Runs per (model × condition)**: **3** with seeds `42, 43, 44`
- **Metrics reported**: `final_answer_accuracy` (judge score), `key_element_coverage`, `total_rounds`, `terminated_by`
- **Outputs**: `results/<study>/<timestamp>/` — raw trajectories + `summary.csv` + `plot.png`

### Code gaps to implement (M4 extension)

Current `run_benchmark.py` only supports a single `max_rounds` and does not checkpoint per round. Add:

1. **`engine/game.py`**
   - `min_rounds_before_answer=0` for Exp 1 (no pressure to wait).
   - `force_final_answer_on_max_rounds=True` for Exp 2 (inject “submit FINAL_ANSWER now” on last turn).
   - Optional: `checkpoint_eval_rounds: List[int]` — after round \(r\), snapshot QA history for offline judge (Exp 1).

2. **`scripts/run_round_curve.py`** (Exp 1)
   - Run up to 30 rounds; after each round \(r\), call judge on a **checkpoint answer**:
     - **Preferred**: one extra Questioner call: “Based on the history so far, reply only with `FINAL_ANSWER: …`”.
     - Record `accuracy_at_round[r]` without stopping the main game.
   - Aggregate: mean ± std over puzzles × seeds per model.

3. **`scripts/run_round_cap_sweep.py`** (Exp 2)
   - For each cap \(C \in \{5,10,15,20,25,30\}\): `max_rounds=C`, force final answer on round \(C\) if not yet submitted.
   - `min_rounds_before_answer` can stay 0; cap is the only limit.

4. **`evaluation/plot_round_studies.py`**
   - Exp 1: line plot — x = round 1–30, y = accuracy, one line per Questioner model, error band (std).
   - Exp 2: line or bar — x = round cap, y = end accuracy, one line per model.

5. **Providers**
   - Cherry-pick or re-implement `qwen_provider.py` from `feature/puzzle-generator-pipeline` on `main`.

---

## Experiment 1 — Accuracy vs conversation length (no progress pressure)

### Intent

Measure whether models **naturally converge** to the correct story as they are allowed more dialogue turns. The Questioner is **not** forced to wait a minimum number of rounds before answering; it may submit `FINAL_ANSWER` early, but we still record accuracy **at every round checkpoint** up to 30.

### Protocol

```
For each questioner_model in {deepseek-r1, qwq-32b, llama3.3:70b}:
  For each puzzle in 11 puzzles:
    For each seed in {42, 43, 44}:
      Run game with max_rounds=30, min_rounds_before_answer=0
      For r = 1 .. 30 (or until natural game end):
        - If game already ended with FINAL_ANSWER at round r' < r: use that answer for all r >= r'
        - Else: obtain checkpoint answer at round r (extra Questioner call on truncated history)
        - Judge checkpoint answer → score[r]
```

### Plot spec

- **Title**: “Final-answer accuracy vs dialogue round (natural pacing)”
- **X**: Round \(1 \ldots 30\)
- **Y**: Mean judge score in \([0, 1]\)
- **Lines**: 3 Questioner models (distinct colors)
- **Shading**: ±1 std across puzzles × seeds
- **Reference**: horizontal line at Oracle-only random baseline (optional, ~0.1)

### Hypotheses (informal)

- Reasoning models show monotonic or step-wise improvement through rounds 5–20.
- Diminishing returns after ~20 rounds for easy puzzles (`turtle_004`, `turtle_010`).

---

## Experiment 2 — Performance under round budget (hard cap)

### Intent

Simulate **resource-limited** play: the agent has at most \(C\) question turns before it must commit to an answer. Tests efficiency under pressure.

### Protocol

```
For each cap C in {5, 10, 15, 20, 25, 30}:
  For each questioner_model:
    For each puzzle × seed (same as Exp 1):
      Run with max_rounds=C, min_rounds_before_answer=0
      On round C if no FINAL_ANSWER yet:
        - System inject: "You have no questions left. Reply with FINAL_ANSWER: ..."
      Judge final answer → score(C)
```

### Plot spec

- **Title**: “End accuracy vs maximum allowed rounds”
- **X**: \(C \in \{5, 10, 15, 20, 25, 30\}\)
- **Y**: Mean judge score at game end
- **Lines**: 3 Questioner models
- **Optional secondary**: grouped bar per cap with error bars

### Hypotheses (informal)

- Large gap between \(C=5\) and \(C=15\) for hard puzzles (`turtle_001`, `turtle_015`).
- Curves plateau by \(C=25\)–\(30\) if the model already exhausted useful questions.

---

## Execution checklist

### Phase A — Prep (done / in progress)

- [x] Pull 6 extra puzzles locally (`turtle_010`–`015`)
- [ ] Add `qwen` provider to `main` (from feature branch)
- [ ] Verify API keys / Ollama models in `.env`
- [x] Smoke test: `run_pilot.py` on `turtle_001` + `turtle_002` with `--mock`

### Phase B — Implement runners

- [x] `evaluation/round_studies.py` — Exp1 curve + Exp2 cap + timing
- [x] `scripts/run_pilot.py` — 2-puzzle pilot with wall-clock + API extrapolation
- [x] Engine: `force_final_answer_on_max_rounds`, `request_final_answer()`
- [x] Tests: `tests/test_round_studies.py`
- [ ] `run_round_curve.py` / `run_round_cap_sweep.py` (standalone CLIs)
- [ ] `plot_round_studies.py`

### Pilot timing (2026-06-11, mock, 2 puzzles)

| Segment | Wall time | Notes |
|---------|-----------|-------|
| Exp1 (30 rounds × 2 puzzles) | ~0.005s | mock only |
| Exp2 (6 caps × 2 puzzles) | ~0.01s | mock only |
| **Pilot total** | **~0.015s** | |

API calls (pilot): Exp1 ≈36 (18/puzzle, ends early) + Exp2 ≈84 → **~120 total**.

Extrapolation to **full study** (11 puzzles × 3 models × 3 seeds, @ 12s/call):

| Study | API calls (est.) | Wall time (est.) |
|-------|------------------|------------------|
| Exp1 | ~1,782 | ~5.9 h |
| Exp2 | ~7,524 | ~25.1 h |
| **Combined** | **~9,306** | **~31 h** |

Run: `python scripts/run_pilot.py --puzzles turtle_001 turtle_002`  
Report: `results/pilot/<timestamp>/pilot_timing.json`

### Phase C — Run studies

```bash
# Exp 1 (example — after scripts exist)
python scripts/run_round_curve.py \
  --puzzles all \
  --questioner-models deepseek-reasoner qwq-32b llama3.3:70b \
  --questioner-providers deepseek qwen ollama \
  --oracle-model gpt-4o \
  --max-rounds 30 \
  --seeds 42 43 44 \
  --output results/exp1_round_curve/

# Exp 2
python scripts/run_round_cap_sweep.py \
  --puzzles all \
  --round-caps 5 10 15 20 25 30 \
  --questioner-models deepseek-reasoner qwq-32b llama3.3:70b \
  --output results/exp2_round_cap/

# Plots
python evaluation/plot_round_studies.py results/exp1_round_curve/ results/exp2_round_cap/
```

### Phase D — Report

- [ ] `results/REPORT.md` — tables + embedded plots
- [ ] Update `AGENTS.md` status when complete

---

## Cost & time estimates

| Item | Estimate |
|------|----------|
| Exp 1 games | 3 models × 11 puzzles × 3 seeds = **99** full games (+ 30 checkpoint calls/game → budget API tokens) |
| Exp 2 games | 6 caps × 3 models × 11 × 3 = **594** games |
| Oracle (gpt-4o) | 99 + 594 ≈ **693** games worth of Oracle calls |

Use `--mock` only for pipeline validation; real study requires live APIs.

---

## Open decisions

1. **Checkpoint cost (Exp 1)**: 30 extra Questioner calls per game is expensive; alternative is judge-only on “best guess so far” every 5 rounds — confirm with Xiaoxuan.
2. **Oracle model**: gpt-4o vs fixed open model (e.g. `deepseek-chat`) for full open-source stack.
3. **Merge `feature/puzzle-generator-pipeline`** into `main` before large runs, or keep puzzle files only.

---

*Next step: implement Phase B scripts, then run Phase C on a 2-puzzle pilot before full 11-puzzle sweep.*
