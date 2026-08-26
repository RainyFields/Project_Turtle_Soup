# TurtleSoup-Creativity: A Dual-Track Benchmark for Evaluating the Associative and Lateral Thinking of LLM Agents

**Project site:** https://iab-agents.github.io/
**Status:** Proposal draft v0.1 — July 28, 2026

---

## Abstract

Turtle Soup (海龟汤, situation puzzles) is a lateral-thinking game in which players are given a short, seemingly paradoxical scenario (the 汤面, "soup surface") and must reconstruct the hidden story (the 汤底, "soup base") — classically by asking yes/no questions. We propose **TurtleSoup-Creativity**, a benchmark that uses turtle soup puzzles to measure the *creative and associative* capabilities of LLM agents, a dimension largely absent from existing puzzle benchmarks that focus on logical consistency or answer accuracy. Our design has two novel components. First, a **solution-space-aware difficulty grading pipeline**: for each 汤面 we sample candidate stories from multiple generator LLMs, deduplicate and cluster them in embedding space, validate cluster representatives with a panel of judge LLMs against an explicit rubric, and grade difficulty by the *structure* of the resulting plausible-solution space (number of valid clusters, their dispersion, and the distance of the canonical 汤底 from the modal cluster). Second, a **dual-track evaluation protocol**: a *convergent* track (recover the intended 汤底 through interactive questioning) and a *divergent* track (generate as many distinct, valid stories as possible), scored with a creativity metric that gates semantic novelty by judged validity, plus a human-interpretable *exploration-style profile* for each agent. We outline a small toy experiment to establish feasibility of the core pipeline before full-scale construction.

---

## 1. Introduction

### 1.1 Why turtle soup?

Most reasoning benchmarks reward *convergence*: there is one correct answer, and the model's job is to reach it. Yet a large part of intelligent behavior — scientific hypothesis generation, debugging, detective work, design — is *abductive and divergent*: constructing many candidate explanations for sparse, surprising observations, then testing and revising them. Turtle soup puzzles are a natural laboratory for exactly this ability:

- The 汤面 is deliberately under-determined: many stories can explain it, but only some are coherent, and only one is the intended 汤底. This makes the *shape of the solution space* — not just the single answer — an object of study.
- The classic interactive format (yes/no questions) externalizes the agent's hypothesis-space search, making the *process* of imagination observable, not just the final answer.
- Puzzles are short, self-contained, language-only, and culturally rich, making them cheap to evaluate at scale.

### 1.2 The gap

Existing turtle-soup and situation-puzzle benchmarks evaluate whether models can *judge guesses correctly* (TurtleBench), *reach the answer efficiently* (SPLAT), or *maintain logical consistency while questioning* (TurtleSoup-Bench). None of them:

1. **Characterize puzzle difficulty by the structure of the solution space.** Existing difficulty labels are crowd-sourced ratings or author intuition. But for a divergent task, difficulty is a property of *how many* coherent stories fit the clues and *where* the intended one sits among them.
2. **Measure creativity as such.** Accuracy and consistency metrics say nothing about whether an agent explores broadly, produces novel-but-valid hypotheses, or merely re-treads the highest-probability story.
3. **Separate convergent from divergent competence.** An agent can be a brilliant hypothesis generator and a poor converger, or vice versa. Existing single-track designs cannot see this distinction.

### 1.3 Our contributions (planned)

1. **A graded turtle soup benchmark** (~200–500 puzzles at full scale; mixture of curated classics, fresh community puzzles, and LLM-drafted/human-verified novel puzzles) in which each puzzle carries a *solution-space profile*: number of distinct plausible story clusters, their embedding-space dispersion, and the position of the canonical 汤底 relative to the modal (most obvious) story cluster.
2. **A dual-track evaluation protocol** — Track A (convergent: recover the 汤底 interactively) and Track B (divergent: enumerate distinct valid stories) — run on the *same* puzzles, so the two competencies can be directly contrasted per model.
3. **A validity-gated creativity metric** combining semantic novelty (embedding distance from the modal story cluster / from other agents' outputs) with multi-judge plausibility scores, avoiding the failure mode where "far = rambling" scores as creative.
4. **Exploration-style profiles** ("agent personality" at the human-interpretable level): breadth-first vs. depth-first questioning, risk appetite, persistence after refutation, and information gain per question, derived from interaction traces.
5. **A public leaderboard** of open-source (and select frontier) agents at https://iab-agents.github.io/.

---

## 2. Literature Review

### 2.1 Turtle soup and situation puzzles as LLM benchmarks

**TurtleBench** (Yu et al., arXiv:2410.05262) collects 1,532 real user guesses from an online turtle soup platform, each annotated for correctness, and evaluates nine LLMs on the *judge* role: given 汤面, 汤底, and a user guess, decide yes/no. It is a strong test of contextual logical reasoning and is refreshingly contamination-resistant (real user data, hidden 汤底), but by construction it measures verification, not generation or exploration — the model never has to imagine anything. Notably, OpenAI's o1-series models did not lead on this benchmark, which the authors attribute to noise introduced by long chain-of-thought.

**SPLAT** (Chen et al., arXiv:2410.06733) introduces 975 situation puzzles at three crowd-annotated difficulty levels and a multi-turn *player–judge* framework where the evaluated LLM asks yes/no questions of a judge model; agreement between judge models and humans exceeds 80%. Key metrics are accuracy, average rounds, and a combined efficiency score; GPT-4 leads at ~42% accuracy, and fine-tuning on SPLAT data transfers to other lateral-thinking benchmarks (RiddleSense, BrainTeaser). SPLAT establishes the interactive protocol we adopt for our convergent track, but its difficulty grading is annotation-based (not solution-space-based) and it scores only convergence.

**TurtleSoup-Bench** (arXiv:2508.10358, AAAI) is the closest in spirit: 800 bilingual puzzles and a Mosaic-Agent evaluation with a multi-dimensional protocol (logical consistency, detail completion, conclusion alignment), framing turtle soup as a probe of *imaginative reasoning* — proactive hypothesis construction in information-sparse environments. It finds a significant LLM–human gap. However, its scoring dimensions still reward faithfulness to the single intended 汤底; it does not measure the breadth or novelty of the hypothesis space an agent explores, nor does it grade puzzles by solution-space ambiguity.

### 2.2 Divergent thinking and creativity in LLMs and agents

**MUTATE / ReDNA** (Park et al., arXiv:2605.28465) is our closest methodological neighbor outside the turtle soup domain: an interactive escape-room-style benchmark where the intuitive solution deliberately fails, forcing agents to discover mechanism-distinct alternative paths. Metrics include distinct-path discovery and an LLM-judged "divergence momentum" (originality, elaboration, groundedness), with 0.84 judge–human pairwise agreement. Frontier models discover far fewer alternative paths than humans (best model 53.6% vs. human 79.9%), and the authors identify a root cause we should expect in turtle soup too: divergent ideation and convergent selection operate under the same conditioning, so unusual hypotheses are filtered out before they surface. Their ReDNA agent (separate diverge and narrow phases) improves path discovery by ~20% — a candidate baseline *intervention* for our benchmark.

Static creativity evaluations adapt psychometric instruments: Torrance-test-style batteries, the Divergent Association Task, and word-divergence games measure fluency/originality/flexibility of text generation; comparative studies find LLMs competitive with average humans on some divergent tasks but with characteristic homogeneity across samples. **CreativityPrism** (arXiv:2510.20091) and reference-based automated creativity scoring (arXiv:2504.15784) offer cross-domain frameworks. The consensus definition across this literature — creativity = *novelty × appropriateness* — directly motivates our validity-gated distance metric: novelty alone (embedding distance) is gameable by incoherence, and appropriateness alone collapses back to accuracy.

### 2.3 LLM-as-judge reliability

Our pipeline leans on LLM judges twice (validating generated traces; judging agent outputs), so judge reliability is a first-class concern. The survey and bias-quantification literature ("Justice or Prejudice?", ICLR 2025; position-bias studies, IJCNLP 2025) documents position bias, verbosity bias, self-preference (a judge favoring outputs of its own family), and inconsistency across phrasings. Mitigations we adopt: rubric-anchored pointwise scoring (not pairwise preference), panels of ≥3 heterogeneous judges with majority/mean aggregation, randomized presentation, and human calibration on a held-out subset with reported judge–human agreement (SPLAT: >80%; MUTATE: 0.84 — our bar is ≥80%).

### 2.4 Positioning

| Benchmark | Interactive? | Measures creativity? | Difficulty grading | Dual track |
|---|---|---|---|---|
| TurtleBench | No (judge role) | No | No | No |
| SPLAT | Yes | No (accuracy/rounds) | Crowd annotation | No |
| TurtleSoup-Bench | Yes | Partially (consistency/completion) | No | No |
| MUTATE | Yes (escape rooms) | Yes (paths, momentum) | No | No |
| **Ours** | **Yes** | **Yes (validity-gated novelty + style)** | **Solution-space structure** | **Yes** |

---

## 3. Research Questions

- **RQ1 (Benchmark construction).** Can multi-model trace generation + embedding clustering + multi-judge validation produce a stable, reproducible *solution-space profile* per puzzle, and does the derived difficulty grade agree with human difficulty judgments?
- **RQ2 (Convergent vs. divergent competence).** Do agents' rankings differ between Track A (recover the 汤底) and Track B (enumerate valid stories)? Is divergent ability predictive of convergent success on high-difficulty (many-cluster) puzzles?
- **RQ3 (Creativity measurement).** Does validity-gated embedding distance correlate with human judgments of creativity better than raw distance or judge scores alone?
- **RQ4 (Exploration style).** Do stable, interpretable exploration-style profiles emerge per model, and do they persist across puzzles and difficulty levels?

---

## 4. Benchmark Construction

### 4.1 Puzzle sourcing

Three sources, tagged in metadata so contamination effects can be analyzed per source:

1. **Curated classics** (e.g., "Albatross soup"): high quality, but assumed contaminated — retained mainly for calibration and memorization analysis.
2. **Fresh community puzzles**: recent puzzles from Chinese/English communities, post-dating model training cutoffs where possible.
3. **Novel LLM-drafted, human-verified puzzles**: an LLM drafts 汤面/汤底 pairs under constraints (surprising surface, coherent hidden story, no supernatural resolution unless flagged); human curators filter for quality and solvability. Target: ≥50% of the final benchmark is novel.

**Memorization check (run on every puzzle, every evaluated model):** prompt the model cold with the 汤面 and ask directly for the 汤底. A near-verbatim hit flags the (model, puzzle) pair; flagged pairs are excluded from that model's creativity scores and reported separately.

### 4.2 Solution-space profiling pipeline

For each puzzle:

1. **Trace generation.** Sample N (~30–50) candidate stories from a *pool of ≥3 heterogeneous generator models* (mix of families and sizes; varied temperatures and prompt framings) to reduce single-generator distribution bias. Each trace is a complete story that purports to explain the 汤面.
2. **Normalization & deduplication.** Canonicalize each trace to a structured summary (who / what happened / why the surface facts obtain), embed with a multilingual sentence encoder, and merge near-duplicates (cosine similarity above threshold θ_dup) so the profile reflects *distinct stories*, not the generators' mode.
3. **Clustering.** Cluster deduplicated embeddings (HDBSCAN or agglomerative with silhouette-based selection). Each cluster = one candidate "story family."
4. **Validity judging.** A panel of ≥3 judge models scores each cluster representative against a fixed rubric (see §4.3). A cluster is *valid* if the panel's aggregated score passes threshold. Human calibration on a subset (§6).
5. **Profile.** The puzzle's solution-space profile is: number of valid clusters **K**, dispersion **D** (mean pairwise distance between valid cluster centroids), modal cluster mass **M** (fraction of raw traces landing in the largest valid cluster), and canonical eccentricity **E** (embedding distance from the 汤底 to the modal cluster centroid).

### 4.3 Validity rubric (judge-facing)

A story is *valid* iff: (a) it entails **every** stated fact in the 汤面, not just most; (b) it is internally coherent (no contradictions, no unexplained coincidences doing the real work); (c) it violates no explicit puzzle constraints (e.g., "no supernatural elements"); (d) it is complete enough that a reader would accept it as a resolution. Judges score (a)–(d) separately on 0–2 scales with mandatory cited evidence from the story; validity = all subscores ≥1 and total above threshold. Panel aggregation: median. Presentation randomized; judges never see which model produced a trace (mitigates self-preference).

### 4.4 Difficulty grading

Difficulty is *track-relative*, resolving the ambiguity-vs-difficulty confound identified in early design discussions:

- **Track A (convergent) difficulty** ↑ with K (bigger haystack), ↑ with E (the intended story is far from the obvious one), ↓ with M when the canonical answer *is* the modal story.
  Proposed grade: `Diff_A = f(K, E, 1−M_canonical)` — initially a simple rank-sum over the three components, three levels (Easy/Medium/Hard) by tercile; refined against human solve rates later.
- **Track B (divergent) difficulty** ↓ with K and D (many far-apart valid stories = easy to be prolific), ↑ when K is small (little room to diverge validly).
  Proposed grade: `Diff_B = f(1/K, 1/D)`.

A key validation target (RQ1): Diff_A should correlate with human solve difficulty (SPLAT-style annotation on a subset); puzzles where the two grades diverge sharply are the most scientifically interesting.

---

## 5. Evaluation Protocol

### 5.1 Track A — Convergent (interactive 汤底 recovery)

Classic play: the agent asks yes/no questions of a programmatic judge (an LLM given the 汤底, answering yes/no/irrelevant per SPLAT/TurtleSoup-Bench protocol), and may propose a full solution at any time, within a question budget (e.g., 25).

Metrics: solve rate (final story matches 汤底 per judge panel), rounds-to-solve, and **per-question information gain** (reduction in entropy over the puzzle's valid-cluster posterior, estimable because we know the solution-space profile — a question is informative if its answer eliminates clusters).

### 5.2 Track B — Divergent (valid-story enumeration)

The agent sees only the 汤面 and must produce up to J (e.g., 10) *maximally different* stories that each fully explain it. No interaction; this isolates pure associative breadth.

Metrics:

- **Coverage**: fraction of the puzzle's known valid clusters hit by at least one of the agent's valid stories (+ credit for *new* valid clusters the profile missed — these are fed back to enrich the benchmark).
- **Validity-gated novelty (creativity score)**: for each agent story s that passes the judge panel, novelty(s) = normalized embedding distance from the modal cluster centroid; creativity(s) = novelty(s) × validity(s). Agent score = mean over its stories. Invalid stories score 0 regardless of distance — distance alone must never be reportable as creativity.
- **Self-diversity**: mean pairwise embedding distance among the agent's own valid stories (does it re-tread one idea or genuinely diverge?).

### 5.3 Exploration-style profile ("personality", human-interpretable)

Derived from Track A interaction logs, reported as a radar profile per model rather than a single score:

- **Breadth vs. depth**: distribution of consecutive questions within the same hypothesis cluster vs. jumps across clusters.
- **Risk appetite**: share of questions probing low-mass (non-modal) clusters.
- **Persistence**: behavior after a "no" — abandon, refine, or repeat.
- **Efficiency**: mean information gain per question.
- **Calibration**: quality of the decision of *when* to commit to a final answer.

We deliberately avoid Big-Five-style trait attribution; the profile is defined entirely in terms of measurable search behavior.

### 5.4 Evaluated systems

Open-source agents first (e.g., Qwen, DeepSeek, Llama families, plus agentic scaffolds like ReDNA-style diverge-then-narrow), with 2–3 frontier APIs as reference points. Scaffold and base model are reported separately so the leaderboard distinguishes "creative model" from "creative harness."

---

## 6. Toy Feasibility Experiment (design)

**Goal:** validate the two riskiest assumptions before building at scale: (i) the solution-space profiling pipeline produces stable, human-plausible cluster structure; (ii) judge panels agree with humans well enough (≥80%) to anchor validity.

**Scale:** 6 puzzles × 2 difficulty intuitions (3 "seems open-ended", 3 "seems constrained"), chosen from fresh community puzzles; 2 of the 6 additionally get a hand-written novel variant to pilot §4.1(3).

**Step 1 — Trace generation.** 3 generator models (one Chinese-strong, one English-strong, one small open model) × ~12 samples each per puzzle (~36 traces/puzzle; ~216 total). Vary temperature {0.7, 1.0} and two prompt framings ("explain the scenario" vs. "invent an unusual but coherent explanation").

**Step 2 — Dedup + clustering.** Embed with a multilingual encoder (e.g., bge-m3 or multilingual-e5); dedup at θ_dup ≈ 0.9; cluster; record K, D, M, E per puzzle. **Stability check:** rerun with a second embedding model and with 50% trace subsamples; require cluster-count agreement within ±1 on ≥4/6 puzzles.

**Step 3 — Judging.** 3 judge models score all cluster representatives (~30–60 judgments) with the §4.3 rubric. Two humans (the project team) independently label the same representatives. **Success criterion:** panel–human agreement ≥80%; inter-judge (model–model) agreement reported; disagreement cases analyzed qualitatively.

**Step 4 — Mini dual-track probe.** Run 2 open-source agents on the 6 puzzles in both tracks (Track A budget 15 questions; Track B J=5). Not for conclusions — only to confirm the harness, logging, and metrics compute end-to-end, and to eyeball whether creativity scores discriminate at all.

**Deliverables:** per-puzzle solution-space profiles with visualizations (2-D projection of trace embeddings colored by cluster and validity), agreement tables, and a go/no-go memo. **Estimated cost:** ~300–500 model calls of modest length — well under $50 of API spend at current open-model pricing, a few days of person-time.

**Go/no-go:** proceed to full construction if the stability check and the ≥80% agreement bar both pass; otherwise iterate on the rubric and canonicalization step first.

---

## 7. Timeline (tentative)

| Phase | Weeks | Output |
|---|---|---|
| Toy experiment | 1–3 | Go/no-go memo, pipeline code |
| Puzzle sourcing + novel generation | 3–8 | 200+ puzzle pool with metadata |
| Full solution-space profiling | 6–10 | Graded benchmark v1 |
| Agent harness + evaluation runs | 8–14 | Dual-track results, style profiles |
| Human studies (calibration + creativity correlation, RQ3) | 10–14 | Agreement + correlation analyses |
| Leaderboard + paper | 14–18 | iab-agents.github.io launch, preprint |

## 8. Risks and Mitigations

- **Judge unreliability / bias** → rubric-anchored pointwise scoring, heterogeneous panels, blinding, human calibration with reported agreement; creativity claims never rest on a single judge.
- **Embedding metric fragility** (novelty depends on encoder choice) → report with two encoders; sanity-check that distance correlates with human "surprisingness" ratings on the calibration subset (RQ3).
- **Contamination** → source tagging, per-model memorization checks, ≥50% novel puzzles.
- **Generator distribution bias in profiling** → multi-model pool, dedup before counting, coverage credit for agent-discovered new clusters (the benchmark self-repairs).
- **Gaming the novelty metric** → validity gate is a hard zero; additionally cap credit for stories in clusters the agent itself already covered (self-diversity is scored separately from novelty).
- **Bilingual drift** (中文/English versions of a puzzle behaving differently) → treat language as a factor in analysis; profile each language version separately.

## 9. References

- Yu et al. *TurtleBench: Evaluating Top Language Models via Real-World Yes/No Puzzles.* arXiv:2410.05262. https://arxiv.org/abs/2410.05262
- Chen, Zhang, Wang, Wu. *Weak-eval-Strong: Evaluating and Eliciting Lateral Thinking of LLMs with Situation Puzzles (SPLAT).* arXiv:2410.06733. https://arxiv.org/abs/2410.06733
- *What to Ask Next? Probing the Imaginative Reasoning of LLMs with TurtleSoup Puzzles (TurtleSoup-Bench, Mosaic-Agent).* arXiv:2508.10358, AAAI. https://arxiv.org/abs/2508.10358
- Park, Baek, Park, Lee. *Beyond One Path: Evaluating and Enhancing Divergent Thinking in Interactive LLM Agents (MUTATE, ReDNA).* arXiv:2605.28465. https://arxiv.org/abs/2605.28465
- *Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge.* ICLR 2025. https://openreview.net/forum?id=3GTtZFiajM
- *Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge.* IJCNLP 2025. https://aclanthology.org/2025.ijcnlp-long.18/
- *CreativityPrism: A Cross-Domain Evaluation Framework for LLM Creativity.* arXiv:2510.20091. https://arxiv.org/html/2510.20091
- *Automated Creativity Evaluation for LLMs: A Reference-Based Approach.* arXiv:2504.15784. https://arxiv.org/html/2504.15784v1
- Torrance Tests of Creative Thinking (background on novelty × appropriateness framing). https://en.wikipedia.org/wiki/Torrance_Tests_of_Creative_Thinking
