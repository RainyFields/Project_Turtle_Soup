# Experiment Plan — TurtleSoup-Creativity Toy Feasibility Study (M6)

**Project**: `turtle-soup-bench`
**Basis**: [`docs/proposals/turtlesoup-creativity-proposal-v0.1.md`](../proposals/turtlesoup-creativity-proposal-v0.1.md), §6 (Toy Feasibility Experiment)
**Status**: Plan draft v0.1 — 2026-07-27. For inspection; no code written yet.
**Relation to existing milestones**: independent of M4a/M4b round studies (`plan.md`); reuses the same engine, providers, and puzzle schema. Proposed milestone code **M6 (creativity-toy)**.

---

## 0. Purpose and success criteria

Validate the two riskiest assumptions of the TurtleSoup-Creativity proposal before full-scale construction:

- **H1 (profile stability)**: multi-model trace generation → embedding dedup → clustering yields a *stable* solution-space profile per puzzle (cluster count agreement within ±1 on ≥4/6 puzzles across encoder swap and 50% subsampling).
- **H2 (judge reliability)**: a 3-model judge panel applying the §4.3 validity rubric agrees with human labels on ≥80% of cluster representatives.

**Go/no-go**: proceed to full benchmark construction iff H1 and H2 both pass. If H1 fails → iterate on canonicalization (Step 3.2) before touching clustering parameters. If H2 fails → iterate on rubric wording and few-shot anchors, not on judge model choice, first.

Secondary (non-gating) goals: end-to-end dual-track harness runs on 2 agents; creativity metric computes and visibly discriminates *something*; per-puzzle visualizations render.

---

## 1. What the repo already provides vs. what must be built

| Need (proposal §) | Existing asset | Gap to close |
|---|---|---|
| Multi-provider LLM calls (§6 Step 1, 3) | `agents/provider_factory.py` — openai / anthropic / deepseek / qwen / zai / gemini / ollama / mock | None; reuse as-is |
| Puzzle store + schema (§4.1) | `data/puzzles/*.json`, `generator/schema.py` | Add metadata fields: `source_type`, `language`, `assumed_contaminated`, `novel_variant_of` |
| Track A interactive play (§5.1) | `engine/game.py` (`TurtleSoupGame`, budgets, forced `FINAL_ANSWER`, qa_history) | Log richer per-turn records for style metrics (§7.4); otherwise reuse |
| LLM judge (§4.3, §5) | `evaluation/judge.py` (single judge, 0–1 vs. 汤底) | New *validity panel*: rubric-based (a)–(d) subscores, ≥3 heterogeneous judges, median aggregation, blinding — new module, don't overload the game judge |
| Batch running / reports | `scripts/run_pilot.py`, `evaluation/study_report_html.py` | New scripts for profiling + Track B; HTML report can follow the same pattern |
| Puzzle generation (§4.1.3) | `generator/` A→E pipeline | Reuse Step C prompts to draft the 2 novel variants; still human-verified via Step E review UI |
| Embeddings / clustering | — none — | New package `profiling/` (see §2) + new deps |

**New dependencies** (`requirements.txt` additions, all pip-installable, no GPU required):
`sentence-transformers` (runs `BAAI/bge-m3` and `intfloat/multilingual-e5-large` locally on CPU/MPS), `scikit-learn` (agglomerative + silhouette), `hdbscan`, `umap-learn` (2-D projection for figures), `numpy`/`pandas` (already implied). If local embedding is too slow on the target machine, fall back to a hosted embedding API behind the same interface (see `profiling/embed.py` design below).

---

## 2. Proposed repo layout (new code)

```text
profiling/                      # solution-space profiling pipeline (§4.2)
├── __init__.py
├── trace_gen.py                # Step 1: sample candidate stories from generator pool
├── canonicalize.py             # Step 2a: story → structured summary (who/what/why)
├── embed.py                    # Step 2b: pluggable encoder interface (bge-m3, e5; API fallback)
├── dedup.py                    # Step 2c: cosine-threshold merge (θ_dup)
├── cluster.py                  # Step 3: HDBSCAN + agglomerative w/ silhouette selection
├── validity.py                 # Step 4: rubric prompt, judge panel, median aggregation, blinding
├── profile.py                  # Step 5: K, D, M, E; Diff_A / Diff_B grades
├── stability.py                # encoder-swap + subsample stability checks
└── viz.py                      # UMAP scatter, per-puzzle profile card (HTML/PNG)

evaluation/
├── track_b.py                  # divergent-track metrics: coverage, gated novelty, self-diversity
├── style_profile.py            # Track A trace → exploration-style features (toy: subset only)
└── memorization.py             # cold 汤底-recall probe per (model, puzzle)

scripts/
├── run_trace_gen.py            # per-puzzle trace generation CLI
├── run_profiling.py            # canonicalize → embed → dedup → cluster → judge → profile
├── run_track_b.py              # Track B agent runs + scoring
├── run_memcheck.py             # memorization probe
└── export_calibration_sheet.py # cluster representatives → CSV/HTML for human labeling

data/
├── creativity/                 # gitignored (like data/generator/): traces, embeddings, judgments
│   └── <puzzle_id>/traces.jsonl · canonical.jsonl · embeddings.npz · clusters.json · judgments.jsonl · profile.json
└── puzzles/                    # +6 toy puzzles (creativity_001…006) + 2 variants (…_v2)

docs/plans/creativity-toy-experiment-plan.md   # this file
results/creativity_toy/         # gitignored: reports, figures, go-no-go memo
```

Configuration goes in `config.yaml` under a new `creativity:` key (generator pool, judge panel, encoder names, thresholds), overridable in `config.local.yaml` per existing convention.

---

## 3. Phase-by-phase plan

### Phase 0 — Infrastructure prep (0.5–1 day)

1. Add dependencies; verify `bge-m3` and `multilingual-e5-large` load and embed a bilingual smoke text on this machine (Apple Silicon → `torch` MPS or CPU; measure sec/100 texts).
2. Extend `generator/schema.py` with optional metadata fields (`source_type ∈ {classic, community, novel}`, `language`, `assumed_contaminated: bool`, `novel_variant_of`); keep backward-compatible defaults so existing `turtle_*`/`refsoup_*` files still validate.
3. Add `creativity:` config block + `.gitignore` entries for `data/creativity/` and `results/creativity_toy/`.
4. `tests/`: schema round-trip test; `embed.py` interface test with a stub encoder; `dedup`/`cluster` unit tests on synthetic vectors (fixed seeds).

**Exit criterion**: `pytest -q` green; embedding smoke test < 60 s for 100 texts.

### Phase 1 — Puzzle selection (1 day, mostly human work)

- Select **6 fresh community puzzles** (post-2025 sources preferred), 3 intuitively *open-ended* (many plausible stories) + 3 intuitively *constrained*. Import via the existing R-branch tooling (`scripts/import_reference_puzzles.py` pattern) into `data/puzzles/creativity_001…006.json` with `source_type: community`. Record the human intuition (`expected_openness: high|low`) in metadata — this is the informal prediction that H1's profiles should confirm or refute.
- For 2 of the 6, draft a **novel variant** with `generator/create` (same surface twist, new hidden story), review through the Step E UI, publish as `creativity_00X_v2.json` with `source_type: novel`, `novel_variant_of` set.
- Do **not** reuse `refsoup_*` classics as primary toy puzzles (assumed contaminated); keep `refsoup_006` only as a debug fixture.
- Run `scripts/run_memcheck.py`: for every (puzzle, model in generator pool ∪ agent pool), cold-prompt with the 汤面 and ask for the 汤底; score near-verbatim recall with the existing judge at high threshold (≥0.8 → flagged). Store flags in `data/creativity/memcheck.json`.

**Exit criterion**: 8 puzzle files validate against schema; memcheck flags recorded (flags don't block the toy run; they annotate it).

### Phase 2 — Trace generation (§6 Step 1) (0.5 day compute)

- **Generator pool** (3 heterogeneous models via existing providers; final choice at run time based on available keys):
  - Chinese-strong: `qwen` provider, `qwen-plus` (or `deepseek-chat`)
  - English-strong: `openai` `gpt-4o` (or `anthropic` claude)
  - Small open: `ollama` `qwen2.5:7b`
- **Sampling matrix per puzzle**: 3 models × 2 temperatures {0.7, 1.0} × 2 framings × 3 samples = **36 traces/puzzle**, ~288 total over 8 puzzles.
  - Framing F1 "explain": “给出一个完整、自洽的故事，解释汤面中的所有事实。” / “Write a complete, coherent story explaining every stated fact.”
  - Framing F2 "unusual": “构造一个不寻常但完全自洽的解释…” / “Invent an unusual but fully coherent explanation…”
- Each trace record (`traces.jsonl`): `{trace_id, puzzle_id, model, provider, temperature, framing, lang, story_text, tokens, ts}`. Prompt language matches puzzle language.
- Retry/timeout handling and `--mock` mode mirror `run_benchmark.py` so the pipeline is testable offline.

**Exit criterion**: ≥30 non-empty, non-refusal traces per puzzle (top up with extra samples if refusals occur).

### Phase 3 — Canonicalize, embed, dedup, cluster (§6 Step 2) (1 day)

1. **Canonicalize** (`canonicalize.py`): one cheap LLM call per trace produces a fixed-slot summary — `{who, what_happened, why_surface_facts_hold, mechanism_tag}` — in the puzzle's language. This is the text that gets embedded (reduces style variance that would otherwise dominate embedding distance). Use one designated canonicalizer model for *all* traces (consistency > diversity here).
2. **Embed** (`embed.py`): primary encoder `bge-m3`; secondary `multilingual-e5-large` (stability check only). Store both in `embeddings.npz`.
3. **Dedup** (`dedup.py`): greedy merge at cosine ≥ θ_dup = 0.90 (sweep 0.85/0.90/0.95 once and eyeball merge quality on one puzzle before fixing). Keep merge map so *raw* trace counts still feed modal mass M.
4. **Cluster** (`cluster.py`): run both HDBSCAN (`min_cluster_size=2`) and agglomerative with silhouette-selected k ∈ [2, 10]; default to agglomerative if HDBSCAN marks >30% of points as noise (likely at n≈30). Record chosen algorithm + params in `clusters.json`.
5. **Stability** (`stability.py`), per puzzle: (a) recluster with the secondary encoder; (b) recluster on 5 random 50% subsamples (fixed seeds). Report cluster-count deltas and adjusted Rand index vs. the primary run.

**H1 pass rule** (per proposal): cluster-count agreement within ±1 on ≥4/6 primary puzzles for both (a) and (b) (use median over subsamples for (b)).

### Phase 4 — Validity judging + human calibration (§6 Step 3) (1–2 days, includes human labeling)

- **Panel**: 3 judges from ≥2 model families, disjoint from generator pool where possible (e.g., `gpt-4o`, `claude` current default, `deepseek-chat`). Judges see: 汤面, puzzle constraints, cluster-representative canonical summary + full story text. They never see model provenance or other clusters (blinding); story order randomized per judge.
- **Rubric prompt** (`validity.py`): four 0–2 subscores with mandatory quoted evidence — (a) entails *every* surface fact, (b) internal coherence, (c) constraint compliance, (d) completeness as a resolution. `valid ⇔ min(subscores) ≥ 1 AND total ≥ 5` (threshold to be sanity-checked against human labels; report sensitivity at total ≥ 4/5/6). Panel aggregation: per-subscore **median**, then apply the rule.
- Expected volume: ~5–10 cluster representatives/puzzle × 8 puzzles ≈ 40–80 judgments × 3 judges.
- **Human calibration**: `export_calibration_sheet.py` emits all representatives (blinded, shuffled) to a sheet; **2 team members label independently** with the same rubric. Report: panel–human percent agreement and Cohen's κ on the binary valid/invalid decision; human–human agreement as ceiling; per-subscore confusion breakdown; qualitative notes on every disagreement.

**H2 pass rule**: panel–human agreement ≥80% (both humans, or vs. adjudicated human consensus). Also report inter-judge (model–model) Fleiss' κ.

### Phase 5 — Profiles, difficulty grades, visualization (0.5 day)

Per puzzle (`profile.py`, primary encoder, valid clusters only):

- **K** = number of valid clusters; **D** = mean pairwise cosine distance between valid-cluster centroids; **M** = fraction of *raw* traces (pre-dedup, via merge map) in the largest valid cluster; **E** = cosine distance from the embedded canonical 汤底 (canonicalized the same way) to the modal-cluster centroid. Also record: which cluster (if any) contains the canonical 汤底.
- **Diff_A** = rank-sum of (K, E, 1−M_canonical) → terciles Easy/Med/Hard; **Diff_B** = rank-sum of (1/K, 1/D). With only 6 primary puzzles, report ranks, not grades, and check ordering against the `expected_openness` intuitions from Phase 1 — that comparison is the RQ1 smoke signal.
- **Viz** (`viz.py`): per puzzle, UMAP 2-D scatter of all trace embeddings — color = cluster, marker = valid/invalid/noise, star = canonical 汤底; one summary table of K/D/M/E/Diff ranks. Output a single self-contained HTML (pattern: `evaluation/study_report_html.py`).

### Phase 6 — Mini dual-track probe (§6 Step 4) (1 day)

Not gating; harness shakedown only. **Agents**: 2 open-source questioners already wired (e.g., `qwen-plus`, `deepseek-chat`; or ollama locals for zero cost).

- **Track A**: reuse `engine/game.py` via `run_benchmark.py` with `--max-rounds 15` on the 6 primary puzzles; Oracle per repo default. Extend the trajectory log with per-turn: question text, oracle answer, and (offline, post-hoc) the question's embedded text — enough to later compute cluster-elimination information gain without changing the engine. For the toy, compute only two style features (`style_profile.py`): breadth (rate of consecutive-question cluster switches, by nearest-cluster assignment of each question embedding) and persistence-after-"no". Full radar profile is out of toy scope.
- **Track B** (`run_track_b.py`): single prompt per puzzle — produce J=5 maximally different complete stories (numbered). Parse, canonicalize, embed, judge each story with the Phase 4 panel, then score (`evaluation/track_b.py`):
  - **Coverage** = |valid clusters hit| / K (hit = story within θ_hit of a centroid, θ_hit tuned so canonical 汤底 hits its own cluster; report θ sensitivity). Stories valid but far from all clusters → logged as *candidate new clusters* (feed back to profile — the self-repair loop from §8 of the proposal, piloted here manually).
  - **Creativity** = mean over valid stories of normalized distance-to-modal-centroid × (panel total / 8); invalid ⇒ 0.
  - **Self-diversity** = mean pairwise distance among the agent's valid stories.

**Exit criterion**: all metrics compute end-to-end from raw logs by one command each; numbers eyeballed for sanity (e.g., F2-"unusual" traces should score higher novelty than F1's on at least most puzzles — a cheap internal validity check).

### Phase 7 — Analysis + go/no-go memo (0.5–1 day)

Deliverable `results/creativity_toy/go_no_go.md` containing: H1 stability tables (cluster counts, ARI), H2 agreement tables (κ, %), per-puzzle profile cards, Diff ranks vs. human intuition, Track A/B toy numbers, cost actuals, and a decision with named next iterations if either H fails. Plus the figure pack (UMAP cards) for the project site.

---

## 4. Key design decisions surfaced for inspection (please review)

1. **Canonicalize-then-embed** (Phase 3.1) is the load-bearing choice: it trades some information loss for style-invariance. Alternative (embed raw stories) is kept one flag away (`--embed-raw`) so the stability check can compare both cheaply.
2. **Single canonicalizer model** for all traces avoids injecting a second source of cross-model variance, at the cost of that model's summarization biases. Accepted for the toy; revisit at scale.
3. **Agglomerative as default over HDBSCAN** at n≈30: HDBSCAN's noise handling is attractive but unstable at this sample size. Decision is data-driven (noise fraction rule, Phase 3.4), recorded per puzzle.
4. **Validity threshold (total ≥ 5)** is a guess; the human calibration sheet doubles as threshold-tuning data. Report agreement at 4/5/6 rather than baking one in.
5. **Judge/generator overlap**: with only ~6 usable API families, complete disjointness may be impossible; blinding + median aggregation is the mitigation, and any overlap is disclosed in the memo.
6. **Information gain metric deferred**: full entropy-over-cluster-posterior needs a question→cluster-answer model; the toy only logs what's needed to build it later (question embeddings + oracle answers). Cheaper proxy (cluster-switch rate) stands in.
7. **Bilingual handling**: toy puzzles run in their source language only; no translation. Bilingual drift (proposal §8) is explicitly out of toy scope.

## 5. Budget and schedule

| Item | Estimate |
|---|---|
| Trace generation | ~288 calls × ~600 tok out |
| Canonicalization | ~288 cheap calls |
| Judging (panel + Track B stories) | ~(80 + 60) × 3 calls |
| Memcheck + Track A (15 rounds × 2 agents × 6) + Track B | ~250 calls |
| **Total API** | **~1,000 modest calls; ≪ $50** at open-model pricing (embedding is local/free) |
| Person-time | ~5–7 working days incl. human labeling (2 × ~2h) |

Suggested calendar: Phases 0–2 in week 1; Phases 3–5 in week 2; Phases 6–7 in week 3 — matching the proposal's weeks 1–3 toy window.

## 6. Toy-scope risks (implementation-level, beyond proposal §8)

- **n≈30 traces is small for clustering** → silhouette/ARI noisy. Mitigation: fixed seeds, report subsample spread, and treat H1's ±1 rule as the only hard claim.
- **Refusals/safety filters on dark puzzle content** (deaths are genre-standard) → top-up sampling in Phase 2; log refusal rates per model (itself useful data).
- **Local embedding perf on this machine** → measured in Phase 0 with an API fallback behind `embed.py`.
- **Track B parse failures** (agent doesn't number stories) → strict output template + one repair-reprompt, then drop with a logged parse-failure flag (a real leaderboard metric later).
- **Two-human calibration is fragile** → report human–human κ as ceiling; if humans disagree >20%, the rubric (not the judges) is the problem — iterate there first.

## 7. Implementation checklist (ordered)

- [ ] Phase 0: deps, schema extension, config block, unit tests
- [ ] Phase 1: 6 community puzzles + 2 novel variants published; memcheck run
- [ ] Phase 2: `run_trace_gen.py`; ≥30 traces/puzzle (mock mode first)
- [ ] Phase 3: canonicalize → embed → dedup → cluster; stability report (H1)
- [ ] Phase 4: validity panel; calibration sheet; human labels; agreement report (H2)
- [ ] Phase 5: profiles K/D/M/E, Diff ranks, UMAP cards, HTML report
- [ ] Phase 6: Track A shakedown (2 agents × 6 puzzles × 15 rounds); `run_track_b.py` + scoring
- [ ] Phase 7: `go_no_go.md` memo + figure pack
