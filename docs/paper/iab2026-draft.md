# Thinking Sideways, Observed: Interpreting the Lateral-Thinking Search Behavior of LLM Agents with Turtle Soup Puzzles

**Target venue:** IAB — Interpreting Agent Behavior, Workshop @ NeurIPS 2026 (https://iab-agents.github.io/)
**Draft:** v0.9 — 2026-09-04 — §5 and abstract filled from the completed 22-puzzle grid (`results/grid_2026_09`, 9 shards, zero failures); flatness-first hook confirmed by the author; per the author's 2026-09-03 rule, §5 reports headline conclusions only. 本文件是内容真源；tex 由本文件重新生成（不打补丁）。

**Status:** awaiting author feedback on v0.9; see "Open questions for the authors" at the end.

---

## Abstract

Give a language-model agent thirty rounds of yes/no questions to crack a lateral-thinking puzzle and it does not keep getting better: on 22 human-played Turtle Soup puzzles, checkpoint accuracy improves only in the first ten rounds and only at scale (Qwen3.5-397B 0.12 → 0.20, then flat; a 4B model stays at 0.05 throughout), and extending the round budget monotonically *hurts* the small model (0.050 → 0.004). Outcome scores cannot say why, so we read the process: each game's questions form a trajectory in association space, whose geometry separates two failure modes that share a score of zero. The small model stalls — its late-game stride shrinks to under half the mid-size model's (0.030 vs 0.082) and it volunteers a final story in 2 of 66 games — while larger models stride twice as far, bank their gains early, and then stop converting exploration into accuracy. We are equally plain about what the geometry does not do: within puzzles, mixed-effects models find no predictive power for stride or drift (LRT p ≥ 0.20), a conclusion unchanged under a surface-only anchor, so we claim trajectory geometry as an interpretive instrument, not a score predictor. A pre-experiment lesson rounds out the method: an unaudited Oracle collapses questions to "irrelevant" and makes every game unwinnable, so agent claims begin with an information audit of the environment. We release the harness, the provenance-enforced puzzle set with an under-determination difficulty measure, and a composite score whose clue-recall and causal-logic halves demonstrably measure different competences.

## 1. Introduction

**Page budget: ~0.9 page.**

- **Open with a puzzle.** *A man's body lies in the desert, clutching half a matchstick; luggage and clothing are scattered around him.* That is all the solver sees. The hidden story: a hot-air balloon was losing altitude, the passengers threw out their luggage and were still too heavy, so they drew lots with matchsticks — and the man who drew the short one was thrown out. The solver recovers this by asking yes/no questions, one per round. **Keep this. A reader who has not seen a Turtle Soup puzzle cannot follow anything that comes after.**
- **Hook** (confirmed on the verified set, 2026-09 grid): give an agent thirty rounds and it stops getting better after ten — at every scale we tested, and the smallest model never improves at all. Outcome metrics can state that flatness but cannot explain it — two agents scoring 0.0 may be failing in opposite ways, one never leaving its first hypothesis, the other leaving the plausible region entirely. Explaining it needs instruments that read the *process*, which is this paper's contribution.
- **Why Turtle Soup.** The game gives the agent a paradoxical scenario (the 汤面 "surface") and hides the story (the 汤底 "base"); the agent asks yes/no questions to reconstruct it. Three properties make it an ideal behavioral microscope: (i) the questioning protocol is a naturally verbalized search trace — no probing or activation access needed, the behavior *is* text; (ii) puzzles are deliberately under-determined, so the *direction* of each associative jump is diagnostic; (iii) games are short, language-only, and cheap to run at scale.
- **The gap** (condensed from our positioning table, §2): prior turtle-soup benchmarks (TurtleBench, SPLAT, TurtleSoup-Bench) score verification correctness, solve efficiency, or consistency with the single intended story. None interprets the search behavior itself.
- **Central hypothesis (H).** An agent's per-round questions, embedded in a semantic space jointly with human word-association norms, form a *trajectory* whose geometry predicts and explains success:
  - **H1 (stalling):** failure trajectories with step size → 0 (successive questions semantically near-identical) identify agents that cannot leave a hypothesis basin; lexical novelty heuristics detect only the verbatim extreme of this mode.
  - **H2 (drifting):** failure trajectories with normal step size but increasing distance from the human association manifold identify agents that explore, but in directions no human path takes; this mode is *invisible* to lexical novelty (synonym-shuffled re-asks look "new").
  - **H3 (predictivity):** trajectory features (step-size profile, human-path distance, their interaction) predict final solve quality beyond outcome-adjacent covariates (rounds used, question count, model size), and the two failure modes have distinct signatures.
- **Contributions.** (1) The flatness result — interaction length buys accuracy only in the first ~10 rounds and only at scale, and budget extension actively harms the smallest model; (2) a behavioral-interpretation framework (trajectory geometry) that separates stalling from unbanked exploration, with an honest account of what it does and does not predict; (3) an open-source dual-agent harness, a **22-puzzle set restricted to puzzles humans have played and solved**, and a composite score whose clue-recall and causal-logic halves demonstrably measure different competences (§5.2); (4) a puzzle-level difficulty measure (**under-determination**) that is independent of rounds used, so it can group an accuracy-versus-rounds analysis without the grouping variable and the axis being the same quantity.

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

**Figures** (all regenerated from the 2026-09 grid, in `docs/paper/figures/`): Figure 2 = `fig_e1_curves.png`, checkpoint accuracy against round on the full 0–1 outcome range, so that flatness reads as flat rather than as noise; Figure 3 = `fig_e3_scatter.png`, stride and drift against best outcome per trace — the direct view of the failure-mode separation, with no 2-D projection that cannot preserve the very distances being claimed. (`fig_e2_caps.png` is available for §5.2 if the layout has room; its content is one sentence of text otherwise.)

### 3.2 Puzzles

A puzzle nobody has solved carries no evidence that its clues suffice, that its solution is unique, or that the intended leap is reachable — an agent scoring zero on one teaches us nothing. Our set is therefore hand-picked from the classic repertoire of a Chinese Turtle Soup community — 22 puzzles that people have actually played and solved, each keeping its source record. Surfaces run 9–108 characters (median 34), solutions 13–200 (median 102), with 97 annotated key clues. Provenance is enforced in code — a verified family and a quarantined generated family, with tests that fail if the two mix — because the grid in §5 ran on an earlier set in which only two of eleven puzzles were real.

Each puzzle carries an **under-determination** score: how far the surface alone leaves you from the solution, measured by sampling twelve cold guesses from the surface with no Oracle feedback and taking the closest. It ranges 0.173–0.577 (median 0.347) over the set and is *not* explained by surface length (r = −0.22, n.s.), so it is available as a puzzle-level covariate — the thing §5.3's mixed-effects model currently lacks.

### 3.3 Outcome scoring: composite, not surface

Judged outcome = **clue recall (70)** + **causal-logic identity (30)**:
- Clue recall: matching against per-puzzle annotated key clues — objective, reproducible, difficulty-banded by clue count.
- Causal logic: an LLM judge rates only whether the causal chain (cause → mechanism → outcome) matches, explicitly instructed to ignore wording; sampled k=3 and averaged, since single ratings are unstable on borderline answers.

Motivation: string matching cannot tell a wrong answer from a right one worded differently — we watched a frontier model reconstruct a hidden causal chain completely and score **0.00**. Conversely the clue half stops "far = creative" gaming: distance without validity scores zero, per the novelty × appropriateness consensus [5, 6, 9, 10].

### 3.4 Association-trajectory instrumentation

Per round *t*: extract question keywords → embed → aggregate to a round vector \(q_t\). Two per-trace signals:
- **Step size** \(s_t = d(q_t, q_{t-1})\): the agent's associative stride (forward-flow analogue [9]).
- **Anchor distance** \(h_t = d(q_t, \mathcal{A})\): distance to a per-puzzle semantic anchor.

Failure-mode classifier (hypothesized signatures): stalling = \(\bar{s} \to 0\), \(h\) flat; drifting = \(\bar{s}\) normal, \(h_t\) increasing. Robustness: report under two encoders; the lexical `question_novelty` metric is retained as the ablation baseline H2 predicts will miss synonym-drift.

**On the anchor, stated plainly.** Ours is built from the puzzle's surface, solution and clues — it is **not** a human association manifold and we no longer describe it as one. Two consequences we measured rather than papered over: a large share of its terms come only from the solution and clues, and clue recall is the outcome, so the two are partly definitionally linked; and rebuilding the anchor from the surface alone flips the sign of the drift slope on a substantial minority of traces. We report both anchors, and treat a SWOW-based version [11] as the correct future form. ⚠️ *The re-run must compute both anchors — computing one means running twice.*

## 4. Experiment Designs

**Page budget: ~1.0 page, including the E3 table.**

### E1 — Round curve (does interaction help, and when does behavior degrade?)

After every round, force a checkpoint answer and score it with the same composite judge as E2 (a single scale, so the two curves can be read side by side); plot accuracy vs. round 1…30. Full grid: the released puzzle set × 3 questioner models × 3 seeds, strong fixed cross-family Oracle. Behavioral reading: where curves plateau, do trajectories stall (H1) or drift (H2)? Prediction: plateau onset co-occurs with step-size collapse for small models, with drift for mid-size reasoning models.

### E2 — Round budget (behavior under pressure)

Hard caps {5, 10, 15, 20, 25, 30} with forced final answer; 1,188 games. Reads: budget-conditioned strategy shifts (do agents front-load broad questions when the cap is short?), and whether composite score vs. cap is concave (diminishing returns) per failure mode.

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

## 5. Results

**Page budget: ~1.2 pages, including Figures 2–3.** All numbers from the 2026-09 grid: the 22-puzzle verified set × {Qwen3.5-4B, Qwen3.6-27B, Qwen3.5-397B-A17B} × 3 seeds, DeepSeek-V3.1 Oracle and logic judge (cross-family, audited 95%), zero failed games. E1 = 198 thirty-round games with a scored checkpoint every round; E2 = 1,188 games across caps {5,10,15,20,25,30}.

### 5.1 More interaction stops helping after ten rounds (E1)

Checkpoint accuracy rises only in the first ~10 rounds, and only for the larger models: Qwen3.5-397B climbs from 0.124 (round 1) to 0.200 (round 10) and then stays between 0.18 and 0.21 through round 30; Qwen3.6-27B rises 0.117 → 0.162 and plateaus at ~0.16. Qwen3.5-4B is flat for the entire game, 0.05–0.06 at every checkpoint (Figure 2, drawn on the full 0–1 range). Twenty further rounds of yes/no evidence — two thirds of the interaction budget — buy no accuracy at any scale.

**Commitment separates the models more than accuracy does.** 27B volunteers a final story in 11/66 games (mean round 11.1) and 397B in 9/66 (round 14.2); 4B commits in 2/66 (round 23.5) — it neither improves nor concludes.

### 5.2 Budget pressure is asymmetric (E2)

End accuracy is insensitive to the round cap for the larger models (397B 0.19–0.21 and 27B 0.14–0.18 across all six caps), but **monotonically harmful for the smallest**: 4B falls from 0.050 at cap 5 to 0.004 at cap 30, with 175 of its 396 games ending by token-budget exhaustion rather than by answer (versus 2/396 for 27B and 0/396 for 397B). Longer games do not help a small model; they give it more rounds in which to fail.

**The two score halves dissociate.** Every model earns proportionally far more of the judged causal-logic half than the clue-recall half: 397B averages 12.6/30 logic against 7.2/70 clues, 27B 10.1 against 6.8, 4B 2.9 against 0.2. Models reach the right causal shape well before — and often without — landing the annotated clue content, so the two subscores measure different competences and the composite's logic half is not redundant with string-level recall.

### 5.3 Trajectory geometry explains the plateau but does not predict the score (E3, H3)

The models occupy different geometric regimes: mean associative stride is 0.049 for 4B against 0.088 (397B) and 0.114 (27B), and in the late game 4B's stride falls to 0.030 — under half of 27B's 0.082 — while it almost never commits. That is the stalling signature of H1: the small model circles a hypothesis basin with shrinking steps. Pooled across models, stride correlates with best checkpoint score (Spearman ρ = 0.23, n = 198); but this is a between-model effect — **within** each model the correlation vanishes (|ρ| ≤ 0.16 for every model and every geometric feature; Figure 3).

The mixed-effects test makes that precise. With puzzle as a random intercept and model tier as a fixed effect, adding the drift slope does not improve fit (LRT p = 0.39), nor does stride × tier (p = 0.20); the puzzle intercept absorbs the variance the geometry seemed to carry. The new puzzle-level covariate sharpens the interpretation: under-determination points the expected way (harder surface → lower score, coef −0.031) but is not significant (p = 0.22) and removes only ~8% of the puzzle variance — the puzzle effect is not merely measured difficulty. **H3 is not supported within-puzzle**, and we accordingly claim trajectory geometry as an interpretive instrument — it says *how* an agent is failing — not as a score predictor.

**Both anchors, as promised (§3.4).** Drift slopes computed from the solution-aware and the surface-only anchor agree in rank (ρ = 0.80) yet flip sign on 38/198 traces; the mixed-effects conclusion is the same under both (surface-only drift LRT p = 0.10). The anchor choice changes individual traces, not the finding.

## 6. Harness Observations

> **作者定稿要求（2026-09-03）：论文只保留最重要的结论与结果，不罗列测试/失败实验。**
> 本节据此从四条裁到两条，控制在四分之一页内。被裁的两条实质已由他处覆盖：
> 「表层评分会误判」→ §3.3 复合评分动机与附录 B 的待测项；
> 「线性可解的题不是好探针」→ §3.2 欠定度分级的理由。
> 同一原则适用于重跑后的 §5：报主结果与失败模式对比，
> pilot 数字、评分 bug、被否决的度量留在 plan/AGENTS，不进论文。

1. **原地打转是真实存在的，而词面指标只看得到一半。**小模型在后期会逐字重复更早的提问；
   词面新颖度能抓到这种极端情形，抓不到用新措辞重问同一假设的情形。
2. **被截断的思考会伪装成行为。**token 预算不足时，模型输出的"提问"是被截断的思维链片段，
   Oracle 对着没有问句的字符串作答。从记录上看，这与"Agent 不会提问"无法区分。
   解码配置是环境的一部分。

## 7. Limitations & Ethics

**Page budget: ~0.2 page.** The anchor is not yet human-derived (§3.4), so H2's framing is descriptive until SWOW norms or collected human traces are in place; we do not equate human-unlike with wrong. Keyword extraction and encoders are themselves models — audited, reported under two encoders. Feedback incorporation, the coordinate that would separate stalling from unbanked exploration most directly, is definable but unmeasured. Judge biases mitigated per [7, 8]. The source site is public, so memorisation probes are required rather than optional — and the two puzzles our difficulty measure rates easiest are the two most widely circulated, which the probe would separate. Puzzles involve death and dark themes; content-flagged.

## 8. Conclusion

Turtle soup turns hypothesis-space search into observable text, and trajectory geometry turns that text into behavioral signatures. An endpoint score projects that whole search onto one number, and for interactive agents the projection destroys exactly what you need to improve them: an agent that stalls and an agent that explores without banking need opposite interventions. Reading the trajectory is how you tell which one you have.

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

## Appendix A — The puzzle set

**Where the puzzles come from.** A puzzle nobody has solved carries no evidence that its clues suffice, that its solution is unique, or that the intended leap is reachable — an agent scoring zero on one teaches us nothing. Our set is hand-picked from the classic repertoire of a Chinese Turtle Soup community: 22 puzzles people have played and solved, each keeping its source record. Every item was read and kept or rejected by hand; rejected were puzzles turning on deduction from stated evidence rather than a lateral reframing, and puzzles whose surfaces were incomplete at the source. Surfaces run 9–108 characters (median 34), solutions 13–200 (median 102).

**How hard are they?** Each puzzle carries an **under-determination** score: give a model the surface alone, with no Oracle and no feedback, let it write twelve complete stories, and take the closest to the real solution. The index is one minus that best guess — large when the surface leaves you far from the answer. Over the set:

| range | count |
|---|---|
| 0.15–0.25 | 5 |
| 0.25–0.35 | 8 |
| 0.35–0.45 | 4 |
| 0.45–0.55 | 4 |
| 0.55–0.65 | 1 |

Median 0.347, quartiles 0.273 and 0.410, full range 0.173–0.577 — single-peaked with a thin hard tail. Easiest: the 海龟汤 story itself (0.17) and the desert matchstick (0.19). Hardest: a fourteen-character surface reading *our heights differ / a flowerpot broke / our heights are the same* (0.58).

Two properties make this usable as a covariate. It describes the puzzle, not any agent's performance on it. And it is independent of rounds used — a difficulty defined as "how many rounds this takes" would make an accuracy-versus-rounds plot confirm itself. It is also not a proxy for surface length (r = −0.22, n.s.), so it carries information the obvious surrogate does not.

**A caveat we report either way.** The two puzzles scoring easiest are the two most widely circulated ones. Their surfaces may be easy to complete not because the inference is short but because the story is in the training data, in which case the measure reads familiarity as much as difficulty. A memorisation probe — asking for the solution with no surface given — separates the two and belongs in any use of this measure.

---

## Appendix B — Measuring agent performance

**What counts as a correct answer.** Judged outcome is **clue recall (70)** plus **causal-logic identity (30)**. Clue recall matches the answer against per-puzzle annotated key clues: objective and reproducible. The logic judge rates only whether cause → mechanism → outcome matches, is told explicitly to ignore wording, and is sampled three times and averaged, since single ratings are unstable on borderline answers. The gap between the two subscores is itself readable: right story, wrong vocabulary.

Clue matching tolerates paraphrase through character-bigram recall, which sets a floor on how short an annotated clue may be — below it only a verbatim match counts, and the score reads vocabulary rather than content. Clues are annotated above that floor.

⚠️ *How much the logic half adds over clue recall alone is measurable and not yet measured: compare the two rankings across the set in the re-run. If they agree, thirty points are buying nothing and clue recall alone is the cleaner scale.*

**Where the accuracy curve comes from.** E1 does not score once at the end. Every round, after the Oracle answers, the Questioner is required to commit its best complete story, and *that* is scored — so each point on the accuracy curve is a full answer written with the evidence available at that round.

⚠️ **GAP — one game, in full.** A four-column table per round: the Questioner's question, the Oracle's 是/不是/与此无关, the story it was forced to commit that round, and that story's score. Without the last two columns the reader cannot see where the curve comes from.

---

## Open questions for the authors (feedback wanted before v0.4)

*(Resolved: v0.1 decisions 2 & 5 — grid ran, Figure 1 real. v0.2 decisions 1 & 5 — abstract/intro now lead with flatness; mixed-effects ran: H3 not supported within-puzzle, so the paper claims geometry as interpretive, not predictive. v0.9: flatness-first hook confirmed by the author on the new grid; Q1 below answered empirically — under-determination is not significant (p = 0.22) and absorbs ~8% of the puzzle variance, so the softened H3 framing stays, now with the covariate test to cite.)*
1. **H1 on the new grid:** stalling now shows as the small model's *low and shrinking* stride (0.049 mean, 0.030 late) rather than a sign inversion — H1 reads cleaner than on the old grid. Any objection to stating H1's confirmation in exactly those terms in the intro?
2. **Human data (still open):** the manifold remains the documented proxy. SWOW-zh sourcing or a small human-trace collection would strengthen H2's between-puzzle claim. Feasible before the deadline?
3. **Title (still open):** "Thinking Sideways, Observed" — alternatives welcome.
4. **Length check:** with §5 refilled, a layout pass on the regenerated tex will say where we stand against 4 pages; §2 is the natural place to trim if over. OK to trim there?
