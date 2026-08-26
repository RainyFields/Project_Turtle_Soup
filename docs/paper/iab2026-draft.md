# Thinking Sideways, Observed: Interpreting the Lateral-Thinking Search Behavior of LLM Agents with Turtle Soup Puzzles

**Target venue:** IAB — Interpreting Agent Behavior, Workshop @ NeurIPS 2026 (https://iab-agents.github.io/)
**Draft:** v0.1 — 2026-08-25 — 4-page workshop format (content sized for ~4 pages + references in NeurIPS style)
**Status:** awaiting author feedback; see "Open questions for the authors" at the end.

---

## Abstract

When an LLM agent fails a lateral-thinking task, outcome metrics report *that* it failed — not *how*. We present a behavioral-interpretation framework built on Turtle Soup (海龟汤, situation puzzles), an interactive game whose yes/no questioning protocol externalizes an agent's hypothesis-space search, turn by turn. Our central hypothesis is that **lateral-thinking failures are legible in the geometry of the interaction trace**: embedding each round's question into a semantic space anchored by human word-association norms separates two failure modes that identical outcome scores conflate — *stalling* (association step size collapsing toward zero: the agent circles one hypothesis) and *drifting* (normal step size but monotonically increasing distance from human association paths). We instantiate the framework in a dual-agent benchmark harness (Questioner vs. solution-holding Oracle), contribute a composite scoring scheme that decouples objective clue recall from judged causal-logic recovery, and design three experiments: round-curve and round-budget studies of how behavior evolves with interaction length, and an association-trajectory study adapting forward-flow and divergent-association psychometrics from human creativity research to agent traces. Pilot observations already exhibit both hypothesized failure modes — including a small model that lapses into verbatim question repetition and a frontier model whose correct causal chain scores zero under surface-matching metrics — and reveal a methodological trap for interactive evaluation at large: a weak Oracle silently converts the task into one that is information-theoretically unsolvable, so the observed "agent failure" is actually environment failure.

---

## 1. Introduction

**Page budget: ~0.9 page.**

- **Hook / problem.** Benchmarks for agentic reasoning overwhelmingly score outcomes (solve rate, accuracy, rounds). For *lateral* thinking — abductive reconstruction of a hidden explanation from sparse, surprising observations — outcomes are especially uninformative: two agents scoring 0.0 may be failing in opposite ways (one never leaves its first hypothesis; one leaves the plausible region entirely). A venue on interpreting agent behavior needs instruments that read the *process*.
- **Why Turtle Soup.** The game gives the agent a paradoxical scenario (the 汤面 "surface") and hides the story (the 汤底 "base"); the agent asks yes/no questions to reconstruct it. Three properties make it an ideal behavioral microscope: (i) the questioning protocol is a naturally verbalized search trace — no probing or activation access needed, the behavior *is* text; (ii) puzzles are deliberately under-determined, so the *direction* of each associative jump is diagnostic; (iii) games are short, language-only, and cheap to run at scale.
- **The gap** (condensed from our positioning table, §2): prior turtle-soup benchmarks (TurtleBench, SPLAT, TurtleSoup-Bench) score verification correctness, solve efficiency, or consistency with the single intended story. None interprets the search behavior itself.
- **Central hypothesis (H).** An agent's per-round questions, embedded in a semantic space jointly with human word-association norms, form a *trajectory* whose geometry predicts and explains success:
  - **H1 (stalling):** failure trajectories with step size → 0 (successive questions semantically near-identical) identify agents that cannot leave a hypothesis basin; lexical novelty heuristics detect only the verbatim extreme of this mode.
  - **H2 (drifting):** failure trajectories with normal step size but increasing distance from the human association manifold identify agents that explore, but in directions no human path takes; this mode is *invisible* to lexical novelty (synonym-shuffled re-asks look "new").
  - **H3 (predictivity):** trajectory features (step-size profile, human-path distance, their interaction) predict final solve quality beyond outcome-adjacent covariates (rounds used, question count, model size), and the two failure modes have distinct signatures.
- **Contributions.** (1) A behavioral-interpretation framework and open-source dual-agent harness; (2) a composite outcome score decoupling objective clue recall from judged causal-logic recovery, exposing when surface metrics mislead; (3) three experiment designs (round curve, round budget, association trajectory) with pilot evidence for both failure modes; (4) a methodological finding for interactive evaluation: Oracle competence must be audited *first*, else agent scores measure the environment.

## 2. Related Work

**Page budget: ~0.5 page. All references verified; links in §References.**

- **Turtle soup as LLM benchmark.** TurtleBench [1]: 1,532 real user guesses, models judge yes/no — verification, not exploration. SPLAT [2]: 975 puzzles, interactive player–judge protocol (we adopt this shape for the convergent track), scored by accuracy/rounds. TurtleSoup-Bench [3]: 800 bilingual puzzles, "imaginative reasoning" framing, multi-dimension scoring — still rewards faithfulness to the single intended story. Our delta: we score the *trajectory*, not only the destination.
- **Divergent thinking in agents.** MUTATE [4] shows frontier agents discover far fewer mechanism-distinct alternative paths than humans and localizes a cause (divergent generation and convergent selection under one conditioning); its diverge-then-narrow agent (ReDNA) is a candidate intervention to test *against our trajectory metrics* — the interpretation question is whether it lengthens steps (fixing H1) or re-anchors toward human paths (fixing H2). Cross-domain creativity evaluations (CreativityPrism [5]; reference-based scoring [6]) supply the novelty × appropriateness consensus our composite score implements.
- **Human creativity psychometrics we adapt.** Forward flow [9] quantifies how far free-association chains travel in semantic space and predicts human creativity; the Divergent Association Task [10] shows pairwise semantic distance among generated words is itself a robust creativity measure, and has been applied directly to LLMs [12]. The Small World of Words norms [11] (12,000+ cues, 90k+ participants; multilingual releases) give us an empirical human association manifold to anchor "human-path distance" — rather than assuming any model embedding is human-like.
- **LLM-as-judge reliability.** Bias catalogues and quantification (CALM [7]; position-bias study [8]) motivate our judge design: rubric-anchored pointwise scoring, ≥3 heterogeneous judges, blinding, and — following our composite design — confining the judge to the one subscore (causal-logic identity) that objective matching cannot reach.

## 3. Framework

**Page budget: ~1.0 page, including one figure and the score formula.**

### 3.1 Task and harness

Dual-agent protocol: a **Questioner** sees only the 汤面 and asks one yes/no question per round; an **Oracle** holds the 汤底 and answers 是/不是/与此无关 (yes/no/irrelevant); the Questioner may commit a final story at any round, or is forced to at the budget. Open-source harness with pluggable model providers (local, gateway, and token-billed large-model sampling — including checkpoints of RL-trained questioners), full trajectory logging, and seeds recorded per game.

**Figure 1 (planned):** one annotated game: 汤面 at left; per-round questions plotted as a trajectory in 2-D projected embedding space; human association norms for the puzzle's cue words shaded as a manifold; a stalling trace (tight loop) and a drifting trace (long path leaving the shaded region) contrasted.

### 3.2 Outcome scoring: composite, not surface

Judged outcome = **clue recall (70)** + **causal-logic identity (30)**:
- Clue recall: matching against per-puzzle annotated key clues — objective, reproducible, difficulty-banded by clue count.
- Causal logic: an LLM judge rates only whether the causal chain (cause → mechanism → outcome) matches, explicitly instructed to ignore wording; sampled k=3 and averaged, since single ratings are unstable on borderline answers.

Motivation (observed, §5): a frontier model reconstructed the hidden story's full causal chain yet scored **0.00** under clue-string matching, while the composite score correctly separated its logic (30/30) from its terminology (28/70). Conversely the gate stops "far = creative" gaming: distance without validity scores zero, per the novelty × appropriateness consensus [5, 6, 9, 10].

### 3.3 Association-trajectory instrumentation

Per round *t*: extract question keywords → embed → aggregate to a round vector \(q_t\). Two per-trace signals:
- **Step size** \(s_t = d(q_t, q_{t-1})\): the agent's associative stride (forward-flow analogue [9]).
- **Human-path distance** \(h_t = d(q_t, \mathcal{H})\): distance to the puzzle's human association set \(\mathcal{H}\), built from SWOW norms [11] seeded with the 汤面's content words (plus, optionally, human player traces where available).

Failure-mode classifier (hypothesized signatures): stalling = \(\bar{s} \to 0\), \(h\) flat; drifting = \(\bar{s}\) normal, \(h_t\) increasing. Robustness: report under two encoders; the existing lexical `question_novelty` metric is retained as the ablation baseline that H2 predicts will miss synonym-drift.

## 4. Experiment Designs

**Page budget: ~1.0 page, including the E3 table.**

### E1 — Round curve (does interaction help, and when does behavior degrade?)

After every round, force a checkpoint answer and score it (clue-recall component only, keeping checkpoints cheap); plot accuracy vs. round 1…30. Full grid: 11 puzzles × 3 questioner models × 3 seeds, strong fixed Oracle. Behavioral reading: where curves plateau, do trajectories stall (H1) or drift (H2)? Prediction: plateau onset co-occurs with step-size collapse for small models, with drift for mid-size reasoning models.

### E2 — Round budget (behavior under pressure)

Hard caps {5, 10, 15, 20, 25, 30} with forced final answer; 594 games. Reads: budget-conditioned strategy shifts (do agents front-load broad questions when the cap is short?), and whether composite score vs. cap is concave (diminishing returns) per failure mode.

### E3 — Association trajectory (the core interpretive study)

For every E1/E2 game: compute \(\{s_t\}, \{h_t\}\); test H1/H2 by clustering failure traces on (step-size profile, human-path profile) and checking the two predicted clusters emerge and align with qualitative annotation of 50 traces (2 annotators); test H3 by predicting final composite score from trajectory features vs. covariate-only baseline (mixed-effects, puzzle and model as random effects).

| Component | Instantiation |
|---|---|
| Keyword extraction | per-round, same extractor for all models (held fixed; audited on 50 rounds) |
| Embedding | multilingual encoder ×2 (agreement reported) |
| Human manifold | SWOW-EN + SWOW-zh cues seeded from 汤面 content words [11] |
| Baselines | lexical novelty (`question_novelty`), rounds-used, model size |
| Predicted dissociation | H1 caught by both lexical & semantic; H2 caught **only** by semantic |

### E4 (exploratory) — Interventions and puzzle structure

(a) ReDNA-style diverge-then-narrow prompting [4] vs. plain prompting: which trajectory feature does it move? (b) Puzzle difficulty by *solution-space structure* (from our companion proposal: cluster multi-model candidate stories; grade by cluster count, dispersion, canonical eccentricity): do trajectory signatures shift on many-cluster vs. single-cluster puzzles? (b) also pilots depth-graded puzzle construction — a strong questioner solving a puzzle in ≤N linear rounds disqualifies it as a lateral-thinking probe.

### Methodological prerequisite — Oracle audit

Before any agent claim: probe candidate Oracles on held-out (question, ground-truth) pairs. Pilot: a 4B Oracle answered 30% correctly (thinking disabled) — collapsing most questions to "irrelevant", after which *no* Questioner can succeed and all scores measure Oracle noise; raising Oracle accuracy 30% → 100% left the 4B Questioner's score unchanged, confirming the environment (not the agent) had been the bottleneck. All experiments fix a ≥90%-accuracy Oracle.

## 5. Pilot Observations (evidence the framework detects something real)

**Page budget: ~0.4 page.** All from the current harness; full logs in the repository.

1. **Stalling exists (H1).** A 4B model in later rounds re-asks earlier questions *verbatim* — the lexical extreme of step-size collapse; caught by `question_novelty`, but only because it is verbatim.
2. **Surface scoring misleads; composite fixes it.** Frontier-model final answer with the correct causal chain: clue-string score 0.00; composite 28/70 clues + 30/30 logic. The gap between the two subscores is itself an interpretive signal (right story, wrong vocabulary).
3. **Thinking-budget truncation masquerades as behavior.** With a 512-token budget, a hybrid reasoning model's visible "questions" were truncated chain-of-thought, and every Oracle reply was "irrelevant" — a failure mode of the *instrumentation* (budget), not the agent; disabling template thinking recovered an 8-round solve (composite 0.58). Behavioral interpretation requires auditing the decoding configuration as part of the environment.
4. **Linear-solvable puzzles are poor probes.** A strong model solved a classic puzzle in 5 straight-line rounds — motivating E4(b)'s structure-graded puzzle bank.

## 6. Limitations & Ethics

**Page budget: ~0.2 page.** Keyword extraction and encoders are themselves models (audited, dual-encoder reporting); SWOW norms are population averages, not a normative standard for "correct" association — distance from them is a *descriptive* behavioral coordinate, and we explicitly do not equate human-unlike with wrong (H2 is about failure *correlation*, tested, not assumed); judge biases mitigated per [7, 8]; puzzles involve death/dark themes — content-flagged; contamination handled by memorization probes and fresh/novel puzzle sourcing.

## 7. Conclusion

Turtle soup turns hypothesis-space search into observable text; trajectory geometry over a human-association anchor turns that text into interpretable behavioral signatures. If H1–H3 hold, "why did the agent fail" becomes a measurement, not a vibe — and the same instruments give RL training on the Questioner (enabled by our token-billed provider for large open models and trained-checkpoint evaluation) a behaviorally grounded reward-shaping target.

---

## References (all verified 2026-08-25; each link checked)

1. Yu, Song, Fang, Shi, Zheng, Wang, Niu, Li. *TurtleBench: Evaluating Top Language Models via Real-World Yes/No Puzzles.* arXiv:2410.05262. https://arxiv.org/abs/2410.05262
2. Chen, Zhang, Wang, Wu. *Weak-eval-Strong: Evaluating and Eliciting Lateral Thinking of LLMs with Situation Puzzles (SPLAT).* arXiv:2410.06733. https://arxiv.org/abs/2410.06733
3. Zhou, Wu, Zhang, Sima, Liu. *What to Ask Next? Probing the Imaginative Reasoning of LLMs with TurtleSoup Puzzles (TurtleSoup-Bench).* arXiv:2508.10358. https://arxiv.org/abs/2508.10358
4. Park, Baek, Park, Lee. *Beyond One Path: Evaluating and Enhancing Divergent Thinking in Interactive LLM Agents (MUTATE, ReDNA).* arXiv:2605.28465. https://arxiv.org/abs/2605.28465
5. Hou, Zhang, Lu, Baghel, Brei, Lu, Jiang, Brahman, Chaturvedi, Chang, Khashabi, Li. *CreativityPrism: A Cross-Domain Evaluation Framework for Large Language Model Creativity.* arXiv:2510.20091. https://arxiv.org/abs/2510.20091
6. Li, Zhu, Xu, Wang, Mao. *Automated Creativity Evaluation for Large Language Models: A Reference-Based Approach.* arXiv:2504.15784. https://arxiv.org/abs/2504.15784
7. Ye, Wang, Huang, Chen, Zhang, Moniz, Gao, Geyer, Huang, Chen, Chawla, Zhang. *Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge (CALM).* ICLR 2025; arXiv:2410.02736. https://arxiv.org/abs/2410.02736
8. Shi, Ma, Liang, Diao, Ma, Vosoughi. *Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge.* IJCNLP-AACL 2025. https://aclanthology.org/2025.ijcnlp-long.18/
9. Gray, Anderson, Chen, Kelly, Christian, Patrick, Huang, Kenett, Lewis. *"Forward Flow": A New Measure to Quantify Free Thought and Predict Creativity.* American Psychologist 74(5), 2019. https://www.semanticscholar.org/paper/ce9343dcd211b798c2697a13abaa0d2dbaa14375
10. Olson, Nahas, Chmoulevitch, Cropper, Webb. *Naming Unrelated Words Predicts Creativity (Divergent Association Task).* PNAS 118(25), 2021. https://www.pnas.org/doi/10.1073/pnas.2022340118
11. De Deyne, Navarro, Perfors, Brysbaert, Storms. *The "Small World of Words" English Word Association Norms for over 12,000 Cue Words.* Behavior Research Methods 51(3), 2019. https://link.springer.com/article/10.3758/s13428-018-1115-7
12. Chen, Ding. *Probing the Creativity of Large Language Models: Can Models Produce Divergent Semantic Association?* Findings of EMNLP 2023; arXiv:2310.11158. https://arxiv.org/abs/2310.11158

---

## Open questions for the authors (feedback wanted before v0.2)

1. **Story check:** the draft leads with *interpretation of failure modes* (fits IAB) and demotes the dual-track creativity benchmark (the July proposal's centerpiece) to E4(b). Is that the right emphasis for this venue, or should the divergent track be a co-equal pillar?
2. **Scope of claims:** should v0.2 commit to running E1–E3 in full for the paper (11×3×3 ≈ $150–200 on Tinker per §cost analysis in plan.md), with E4 as "future work" — or present E1–E2 results + E3 design only?
3. **Human data:** H2 needs the human association manifold. SWOW-EN is verified; a Chinese SWOW equivalent needs sourcing (the zh norms in the SWOW family exist but I have not yet verified coverage for our puzzle vocabulary). Is collecting a small set of human player traces (e.g., 5 humans × 6 puzzles) feasible for you within the timeline?
4. **Naming:** current running title "Thinking Sideways, Observed" — alternatives: "Trace of a Sideways Thought", "TurtleSoup-Trace". Preference?
5. **Figure 1** requires a real trajectory projection — fine to build from E1 pilot data on 2 models × 3 puzzles before full runs?
