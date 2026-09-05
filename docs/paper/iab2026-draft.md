# Thinking Sideways, Observed: Interpreting the Lateral-Thinking Search Behavior of LLM Agents with Turtle Soup Puzzles

**Target venue:** IAB — Interpreting Agent Behavior, Workshop @ NeurIPS 2026 (https://iab-agents.github.io/)
**Draft:** v0.13 — 2026-09-05 — **acceptance pass on the round-2 review** (`reviews/2026-09-05_simulated_review_v0.12.md`: A "yes with minor revision", B "borderline leaning accept, editing alone suffices", C "lean accept"). One spine now runs abstract → contributions → conclusion: *one flat score hides two opposite failures; geometry exposes circling, the checkpoint-commitment record exposes abandoning, and neither is visible without an audited environment.* Structural: checkpoint protocol promoted to §3.2 as a named instrument; contributions reordered (instrument pair → audit doctrine ×2 → operationalized patterns → artifacts); hypotheses reframed as questions Q1–Q3 with verdicts; §5 roadmap; LMM coefficients/estimator/permutation-spec/judge-scale moved to Appendix B; anchor caveat consolidated. New evidence in text: per-game pattern criteria + counts (4B 39 circling / 1 abandoning; 397B 6 / 12; zero overlap), solution-grade (≥0.5) cross-tab (397B commits 1/6, four end < half peak; 27B commits 3/4 keeping ~0.83), clustered stride CIs (late 0.030 [0.021,0.039] vs 0.082 [0.065,0.098], malformed-exclusion on the quoted statistic), Δ(r10→30) with clustered CIs, E1 no-budget/no-early-termination statement, corrected finding-4 inference (endpoint scores cannot attribute failure; audit+intervention licenses it), Oracle-error exposure (~1 wrong answer/30-round game) in Limitations. Figures: fig1a round-10 rule + early-rise inset, cluster-bootstrap bands; fig1b commitment-coded markers + solution-grade rule (kept-half line dropped); fig2a replaced by per-tier stride strips with mean±CI; fig3 (worked game) promoted to main text beside fig2; all QA audits pass. Main text ends exactly at page 4 (8-page PDF). Prior: v0.12 — 2026-09-04 — **major concerns of the simulated review addressed** (report: `reviews/2026-09-04_simulated_review_v0.11.md`; analyses: `scripts/review_response_analyses.py` → `figures/review_response.json`). Substantive corrections the new analyses forced: ① the **retention/"find-and-lose equilibrium" claim is withdrawn as a positive finding** — observed retention (0.69–0.76, bootstrap CIs ±≈0.08, estimator = mean per-game final/sustained-peak ratio) is *not* significantly below a within-game permutation (jitter-only) null of 0.79–0.84 (p ≥ 0.09); §5.1 now reports it as inconclusive, and abandonment rests on commitment records + transcripts. ② the **4B budget decline is reattributed to the harness**: exhaustion rises 0/66→63/66 across caps and non-exhausted 4B accuracy does not decline (0.05–0.09); this also resolves the E1-vs-E2 round-30 discrepancy. ③ **circling survives the truncation-artifact check** (17% of 4B questions malformed vs ~1%; excluding them, mean stride 0.049→0.056, still < half of 27B's) — reported in §5.3. ④ "scale" → **model tier** everywhere, with the generation/MoE confound stated. ⑤ abstract finding (4) now cites the reported 30%→100% Oracle pilot; audit protocol, per-candidate numbers, full pipeline spec (jieba / bge-small-zh-v1.5 / cosine / GLM cold guesses), token budgets (2048/call, 50k/game, thinking off), judge settings (2 samples, 86% exact agreement), subscore correlations (ρ = 0.30/0.35/0.06), early-commit rule, and an artifact statement added to Appendix B. ⑥ Table 1 fully translated + round-4 row added; glosses for 汤面/汤底/是不是/与此无关. ⑦ mixed model fully specified with coefficient CIs incl. stride main effect (β −0.010 [−0.035,0.014] p=0.42; surface drift p=0.097 → abstract says p > 0.09); "vanishes" → "not detected". ⑧ scaffolding stripped; figures regenerated compact (5.2×1.7in design, ≥5pt glyphs, all QA pass); main text ends exactly at page 4. Prior: v0.11 — **reframed around the author's two-point summary + nature-figure rebuild.** Center of the paper per author (2026-09-04 discussion): ① 任务失败不是预算或能力不足，而是无效探索（探不到 = circling；探到不沉淀 = abandoning）——量化证据 = peak-retention 统计（`scripts/analyze_peak_retention.py`：sustained-peak 保留率 0.69–0.76 与规模无关，规模只抬峰值 3.5×）；② 两种行为模式在几何空间与语言空间联合识别（几何看全、词面只看一半）。术语从 stalling/unbanked 统一为 **circling/abandoning**；H1–H3 保留为设计假设并在引言给出裁决（H1✓ 作为 circling，H2 drift ✗，abandoning 为未假设的新模式，H3 ✗）。§6 并入 §5.3/§7。图重制（见下方 Figures）。Main text ends exactly at page 4 (References at char 0 of p5). Prior: v0.10 — **nature-polish pass** (nature-polishing skill + the author's NeurIPS 2024 paper as the voice exemplar): abstract restructured to enumerated findings; em dashes removed from prose; sentences split to one proposition each; terminology locked (stride / anchor distance / 4B–27B–397B / accuracy = composite÷100). Consistency-sweep fixes: abstract–§5 precision drift (0.124/0.200 everywhere), logic samples corrected to k=2 as actually run, H2's verdict now stated in §5.3 (drift slopes ≈ 0 at every scale; stalling dominates), stale §3.2/App-B claims repaired, figure numbering aligned (Fig 1 = E1 curves, Fig 2 = E3 scatter). Main text still ends exactly at page 4. Prior state (v0.9): §5/abstract filled from `results/grid_2026_09`, App B worked example, trim pass. 本文件是内容真源；tex 由本文件重新生成（不打补丁）。

**Status:** awaiting author feedback on v0.9; see "Open questions for the authors" at the end.

---

## Abstract

*(v0.10, nature-polish pass; enumerated-findings structure per the author's NeurIPS 2024 paper.)*

Interactive agents are usually evaluated by endpoint scores, yet a score records where a search ended, not how it moved. We study this gap in Turtle Soup, a lateral-thinking game in which an agent must reconstruct a hidden story through yes/no questions. We ran three Qwen models (4B, 27B, 397B) on 22 human-played puzzles, scoring a forced checkpoint answer every round and embedding each round's question to form an association trajectory. We found that: (1) the flat accuracy curve is not a resource limit: gains stop after round ten at every scale (397B 0.124 → 0.200, then flat; 4B flat at 0.05–0.06), longer budgets monotonically *hurt* the smallest model (0.050 → 0.004), and the plateau is an equilibrium of finding and losing: models keep only 0.69–0.76 of the understanding they had held across two consecutive checkpoints, a retention scale leaves unchanged even as it raises the peaks 3.5-fold; (2) two behavioral patterns underlie this, read jointly from geometry and language: the small model *circles* (late-game stride 0.030 vs the mid-size model's 0.082; 2 of 66 games committed), whereas larger models *abandon*, reaching the solution mid-game and then failing to keep or commit it; (3) within puzzles, mixed-effects models find no predictive power for stride or drift (likelihood-ratio tests, p ≥ 0.20), a conclusion unchanged under a surface-only anchor, so the geometry is an interpretive instrument rather than a score predictor; and (4) an unaudited Oracle collapses questions to "irrelevant" and makes every game unwinnable, so agent claims must begin with an information audit of the environment. We release the harness, a provenance-enforced puzzle set with an under-determination difficulty measure, and a two-part score whose clue-recall and causal-logic halves demonstrably measure different competences.

## 1. Introduction

**Page budget: ~0.9 page.**

- **Open with a puzzle.** *A man's body lies in the desert, clutching half a matchstick; luggage and clothing are scattered around him.* That is all the solver sees. The hidden story: a hot-air balloon was losing altitude, the passengers threw out their luggage and were still too heavy, so they drew lots with matchsticks — and the man who drew the short one was thrown out. The solver recovers this by asking yes/no questions, one per round. **Keep this. A reader who has not seen a Turtle Soup puzzle cannot follow anything that comes after.**
- **Hook** (confirmed on the verified set, 2026-09 grid): give an agent thirty rounds and it stops getting better after ten — at every scale we tested, and the smallest model never improves at all. Outcome metrics can state that flatness but cannot explain it — two agents scoring 0.0 may be failing in opposite ways, one never leaving its first hypothesis, the other leaving the plausible region entirely. Explaining it needs instruments that read the *process*, which is this paper's contribution.
- **Why Turtle Soup.** The game gives the agent a paradoxical scenario (the 汤面 "surface") and hides the story (the 汤底 "base"); the agent asks yes/no questions to reconstruct it. Three properties make it an ideal behavioral microscope: (i) the questioning protocol is a naturally verbalized search trace — no probing or activation access needed, the behavior *is* text; (ii) puzzles are deliberately under-determined, so the *direction* of each associative jump is diagnostic; (iii) games are short, language-only, and cheap to run at scale.
- **Central hypothesis (H).** An agent's per-round questions, embedded in a semantic space jointly with human word-association norms, form a *trajectory* whose geometry predicts and explains success:
  - **H1 (stalling):** failure trajectories with step size → 0 (successive questions semantically near-identical) identify agents that cannot leave a hypothesis basin; lexical novelty heuristics detect only the verbatim extreme of this mode.
  - **H2 (drifting):** failure trajectories with normal step size but increasing distance from the human association manifold identify agents that explore, but in directions no human path takes; this mode is *invisible* to lexical novelty (synonym-shuffled re-asks look "new").
  - **H3 (predictivity):** trajectory features (step-size profile, human-path distance, their interaction) predict final solve quality beyond outcome-adjacent covariates (rounds used, question count, model size). *(Trimmed in tex to one clause for space.)*
- **Contributions** (reframed 2026-09-04 per author's two-point summary). (1) An explanation of the flat curve: task failure is driven neither by round budget nor by model capability alone, but by ineffective exploration; scale raises what a model momentarily finds, not what it keeps (retention 0.69–0.76 at every scale, from `scripts/analyze_peak_retention.py` → `peak_retention.json`); (2) two behavioral patterns, **circling** and **abandoning**, identified jointly in geometry space and in language space, with an honest account of what the geometry does and does not predict; (3) an open-source dual-agent harness, a **22-puzzle set restricted to puzzles humans have played and solved**, and a composite score whose halves demonstrably measure different competences (§5.2); (4) a puzzle-level difficulty measure (**under-determination**) independent of rounds used, so it can group an accuracy-versus-rounds analysis without circularity.
- **H verdicts** (stated in intro): H1 confirmed as circling; H2's drift rejected; a second, unhypothesized pattern (abandoning) revealed; H3 not supported.

## 2. Related Work

**Page budget: ~0.35 page (trimmed 2026-09-04 to hit 4 pages). All references verified; links in §References.**

Existing turtle-soup benchmarks — TurtleBench [1], SPLAT [2] (whose interactive player–judge protocol we adopt), TurtleSoup-Bench [3] — score verification accuracy, solve efficiency, or faithfulness to the intended story: the destination, where we score the trajectory. MUTATE [4] shows frontier agents find far fewer mechanism-distinct paths than humans; its diverge-then-narrow agent (ReDNA) is a natural intervention to test against our metrics. The instrument itself adapts forward flow [9] and the Divergent Association Task [10] from human psychometrics — semantic travel as a measure, applied to LLMs in [12] — with the Small World of Words norms [11] as the human anchor ours is not yet (§3.4). Judge-bias catalogues (CALM [7]; position bias [8]) shape the scoring: the model judge is confined to the one subscore objective matching cannot reach. (Cut for space, recoverable from git: CreativityPrism [5] and reference-based creativity scoring [6] as the novelty × appropriateness consensus behind the composite.)

## 3. Framework

**Page budget: ~1.0 page, including one figure and the score formula.**

### 3.1 Task and harness

Dual-agent protocol: a **Questioner** sees only the 汤面 and asks one yes/no question per round; an **Oracle** holds the 汤底 and answers 是/不是/与此无关 (yes/no/irrelevant); the Questioner may commit a final story at any round, or is forced to at the budget. Open-source harness with pluggable model providers (local, gateway, and token-billed large-model sampling — including checkpoints of RL-trained questioners), full trajectory logging, and seeds recorded per game.

**Figures** (v0.11, rebuilt with the nature-figure skill; source `docs/paper/figures/make_figures.py`, collision/alignment audits pass): Figure 1 = `fig1_flatness.pdf`, (a) E1 accuracy curves with 95% CI on the full 0–1 range + (b) final vs sustained-peak scatter with kept-all / kept-half references — the finding-and-losing equilibrium in one view; Figure 2 = `fig2_geometry.pdf`, (a) stride vs best outcome (circling regime) + (b) drift slope vs best outcome (H2/H3 negatives). Palette: scale-ordered blues, red reserved for references; Arial 7pt, editable type. (Older `fig_e1_curves.png`/`fig_e3_scatter.png` from analyze_grid.py remain for analysis use.)

### 3.2 Puzzles

A puzzle nobody has solved carries no evidence that its clues suffice, that its solution is unique, or that the intended leap is reachable — an agent scoring zero on one teaches us nothing. Our set is therefore hand-picked from the classic repertoire of a Chinese Turtle Soup community — 22 puzzles that people have actually played and solved, each keeping its source record. Surfaces run 9–108 characters (median 34), solutions 13–200 (median 102), with 97 annotated key clues. Provenance is enforced in code, with a verified family, a quarantined generated family, and tests that fail if the two mix (an earlier pilot set had mixed the two, with only two of eleven puzzles real).

Each puzzle carries an **under-determination** score: how far the surface alone leaves you from the solution, measured by sampling twelve cold guesses from the surface with no Oracle feedback and taking the closest. It ranges 0.173–0.577 (median 0.347) over the set and is *not* explained by surface length (r = −0.22, n.s.), so it is available as a puzzle-level covariate — the thing §5.3's mixed-effects model currently lacks.

### 3.3 Outcome scoring: composite, not surface

Judged outcome = **clue recall (70)** + **causal-logic identity (30)**:
- Clue recall: matching against per-puzzle annotated key clues — objective, reproducible, difficulty-banded by clue count.
- Causal logic: an LLM judge rates only whether the causal chain (cause → mechanism → outcome) matches, explicitly instructed to ignore wording; sampled and averaged (k=2 in the reported grid), since single ratings are unstable on borderline answers.

Motivation: string matching cannot tell a wrong answer from a right one worded differently — we watched a frontier model reconstruct a hidden causal chain completely and score **0.00**. Conversely the clue half stops "far = creative" gaming: distance without validity scores zero, per the novelty × appropriateness consensus [5, 6, 9, 10].

### 3.4 Association-trajectory instrumentation

Per round *t*: extract question keywords → embed → aggregate to a round vector \(q_t\). Two per-trace signals:
- **Step size** \(s_t = d(q_t, q_{t-1})\): the agent's associative stride (forward-flow analogue [9]).
- **Anchor distance** \(h_t = d(q_t, \mathcal{A})\): distance to a per-puzzle semantic anchor.

Failure-mode classifier (hypothesized signatures): stalling = \(\bar{s} \to 0\), \(h\) flat; drifting = \(\bar{s}\) normal, \(h_t\) increasing. Robustness: report under two encoders; the lexical `question_novelty` metric is retained as the ablation baseline H2 predicts will miss synonym-drift.

**On the anchor, stated plainly.** Ours is built from the puzzle's surface, solution and clues — **not** a human association manifold, and we no longer describe it as one. Its terms overlap the clue set that defines the outcome, and rebuilding it from the surface alone flips the drift slope's sign on a minority of traces (quantified in §5.3); we therefore report both anchors, and treat a SWOW-based version [11] as the correct future form.

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
| Anchor | proxy from surface/solution/clues, both variants reported (§3.4); SWOW-based version [11] is the intended future form |
| Baselines | lexical novelty (`question_novelty`), rounds-used, model size |
| Predicted dissociation | H1 caught by both lexical & semantic; H2 caught **only** by semantic |

### E4 (exploratory) — Interventions and puzzle structure

(a) ReDNA-style diverge-then-narrow prompting [4] vs. plain prompting: which trajectory feature does it move? (b) Puzzle difficulty by *solution-space structure* (from our companion proposal: cluster multi-model candidate stories; grade by cluster count, dispersion, canonical eccentricity): do trajectory signatures shift on many-cluster vs. single-cluster puzzles? (b) also pilots depth-graded puzzle construction — a strong questioner solving a puzzle in ≤N linear rounds disqualifies it as a lateral-thinking probe.

### Methodological prerequisite — Oracle audit

Before any agent claim: probe candidate Oracles on held-out (question, ground-truth) pairs. Pilot: a 4B Oracle answered 30% correctly (thinking disabled) — collapsing most questions to "irrelevant", after which *no* Questioner can succeed and all scores measure Oracle noise; raising Oracle accuracy 30% → 100% left the 4B Questioner's score unchanged, confirming the environment (not the agent) had been the bottleneck. All experiments fix a ≥90%-accuracy Oracle.

## 5. Results

**Page budget: ~1.2 pages, including Figures 1–2.** All numbers from the 2026-09 grid: the 22-puzzle verified set × {Qwen3.5-4B, Qwen3.6-27B, Qwen3.5-397B-A17B; hereafter 4B, 27B, 397B} × 3 seeds, DeepSeek-V3.1 Oracle and logic judge (cross-family, audited 95%; two logic samples per rating), zero failed games. Accuracy denotes the composite score rescaled to [0,1]. E1 = 198 thirty-round games with a scored checkpoint every round; E2 = 1,188 games across caps {5,10,15,20,25,30}.

### 5.1 More interaction stops helping after ten rounds (E1)

Checkpoint accuracy rises only in the first ~10 rounds, and only for the larger models: Qwen3.5-397B climbs from 0.124 (round 1) to 0.200 (round 10) and then stays between 0.18 and 0.21 through round 30; Qwen3.6-27B rises 0.117 → 0.162 and plateaus at ~0.16. Qwen3.5-4B is flat for the entire game, 0.05–0.06 at every checkpoint (Figure 2, drawn on the full 0–1 range). Twenty further rounds of yes/no evidence — two thirds of the interaction budget — buy no accuracy at any scale.

**Commitment separates the models more than accuracy does.** 27B volunteers a final story in 11/66 games (mean round 11.1), 397B in 9/66 (14.2), and 4B in 2/66 (23.5); the smallest neither improves nor concludes.

**The plateau is an equilibrium of finding and losing, not stagnation.** Each game's best checkpoint sits far above its last (Figure 1b). Because rewording alone can swing one checkpoint's score, we measure a *sustained* peak, the best value held over two consecutive checkpoints; even so, models end with only 0.69–0.76 of what they had demonstrably reached, and 18–20 of each model's 66 games end below half their sustained peak. Scale raises the sustained peak 3.5-fold (0.084 → 0.296) but leaves retention unchanged: capability buys higher finds, not better keeping. (Raw peaks: 0.386/0.314/0.146 vs finals 0.191/0.165/0.050; `peak_retention.json`.)

### 5.2 Budget pressure is asymmetric (E2)

End accuracy is insensitive to the round cap for the larger models (397B 0.19–0.21 and 27B 0.14–0.18 across all six caps), but **monotonically harmful for the smallest**: 4B falls from 0.050 at cap 5 to 0.004 at cap 30, with 175 of its 396 games ending by token-budget exhaustion rather than by answer (versus 2/396 for 27B and 0/396 for 397B). Longer games do not help a small model; they give it more rounds in which to fail.

**The two score halves dissociate.** Every model earns proportionally far more of the judged causal-logic half than the clue-recall half: 397B averages 12.6/30 logic against 7.2/70 clues, 27B 10.1 against 6.8, 4B 2.9 against 0.2. Models reach the right causal shape well before — and often without — landing the annotated clue content, so the two subscores measure different competences and the composite's logic half is not redundant with string-level recall.

### 5.3 Two patterns: circling and abandoning (E3)

The models occupy different geometric regimes: mean stride is 0.049 for 4B against 0.088 (397B) and 0.114 (27B), and in the late game 4B's stride falls to 0.030, under half of 27B's 0.082, while it almost never commits. That is H1's signature, which we name **circling**: shrinking orbits of one hypothesis basin, with a sustained peak (0.084) showing the model never finds a solution to lose. The larger models fail in the opposite way, by **abandoning**: they find (sustained peak ≥0.5 in 4–6 of 66 games each) and then fail to keep or commit (§5.1). H2's drifting signature, by contrast, barely appears: drift slopes cluster near zero at every scale (Figure 2b). The second real pattern is abandonment, which the hypothesized drift did not anticipate.

**The same two patterns read differently in language space.** Circling is only half-visible to lexical novelty: verbatim re-asks in late rounds are caught, but the same games earlier re-ask one hypothesis in fresh words, which lexical metrics score as new and only the geometry detects. Abandoning is invisible to lexical measures altogether; it shows in commitment behavior and checkpoint dynamics (§5.1), and Appendix B walks one game whose round-10 checkpoint story *is* the solution, later abandoned.

Pooled across models, stride correlates with best checkpoint score (Spearman ρ = 0.23, n = 198), but this is a between-model effect; **within** each model the correlation vanishes (|ρ| ≤ 0.16 for every model and feature; Figure 2).

The mixed-effects test makes that precise. With puzzle as a random intercept and model tier as a fixed effect, adding the drift slope does not improve fit (LRT p = 0.39), nor does stride × tier (p = 0.20); the puzzle intercept absorbs the variance the geometry seemed to carry. The new puzzle-level covariate sharpens the interpretation: under-determination points the expected way (harder surface → lower score, coef −0.031) but is not significant (p = 0.22) and removes only ~8% of the puzzle variance — the puzzle effect is not merely measured difficulty. **H3 is not supported within-puzzle**, and we accordingly claim trajectory geometry as an interpretive instrument — it says *how* an agent is failing — not as a score predictor.

**Both anchors, as promised (§3.4).** Drift slopes computed from the solution-aware and the surface-only anchor agree in rank (ρ = 0.80) yet flip sign on 38/198 traces; the mixed-effects conclusion is the same under both (surface-only drift LRT p = 0.10). The anchor choice changes individual traces, not the finding.

## 6. Harness Observations（v0.11 起并入正文：条 1「词面指标只看一半」→ §5.3 语言空间段；条 2「截断思考伪装成行为」→ §7 Limitations 的 harness-trap 段。本节在 tex 中已不存在，此处仅存原文备考。）

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

**Page budget: ~0.2 page.** The anchor is not yet human-derived (§3.4), so H2's framing is descriptive until SWOW norms or collected human traces are in place; we do not equate human-unlike with wrong. Keyword extraction and encoders are themselves models; feedback incorporation — the coordinate that would separate stalling from unbanked exploration most directly — is definable but unmeasured. The source site is public, so memorisation probes are required rather than optional: the two puzzles our difficulty measure rates easiest are the two most widely circulated. Puzzles involve death and dark themes; content-flagged.

## 8. Conclusion

Turtle Soup turns hypothesis-space search into observable text, and trajectory geometry turns that text into behavioral signatures. An endpoint score projects the whole search onto one number, discarding exactly what improving an interactive agent requires: circling and abandoning agents need opposite interventions, and only the trajectory tells you which you have.

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

**Does the logic half earn its thirty points?** On the full grid, yes: the two halves dissociate for every model (§5.2), with each model earning a several-fold larger share of the logic half than of the clue half. If the two rankings had agreed, clue recall alone would have been the cleaner scale; they do not.

**Where the accuracy curve comes from.** E1 does not score once at the end. Every round, after the Oracle answers, the Questioner is required to commit its best complete story, and *that* is scored — so each point on the accuracy curve is a full answer written with the evidence available at that round.

**One game, worked.** Puzzle `refsoup_021` (surface: a stormy night, a run-down temple, two photographs on the wall that seem to stare; by morning the narrator sees only two windows; solution: 墙上根本没有照片，是有人贴着窗户往里看), played by Qwen3.5-397B, seed 2. Six of thirty rounds; every cell verbatim from the log, stories abridged to the clause carrying the hypothesis.

| 轮 | Question (abridged) | 答 | Committed story (abridged) | score (clue + logic) |
|---|---|---|---|---|
| 1 | 照片里的是人吗？ | 是 | 那两张"照片"…是两个被钉死或封在墙洞里的人 | 0.12 (0 + 12) |
| 3 | 主角第二天醒来时，还在那座寺庙里吗？ | 是 | 所谓的"两张照片"其实是两扇窗户…昏暗光线下…误看成了照片 | 0.91 (70 + 21) |
| 10 | "两扇窗户"是因为相框玻璃破碎脱落、变成通透的洞口吗？ | 不是 | 那根本不是照片，而是…躲在窗户后面（或贴在窗玻璃外侧）的人脸 | **1.00 (70 + 30)** |
| 11 | 是因为照片被取走、露出了后面原本就存在的窗户吗？ | 不是 | 昨晚"盯着他的人像"，其实是**窗外的人** | **1.00 (70 + 30)** |
| 19 | 照片里的人像实际上是躲在照片后面的真人吗？ | 不是 | 窗户洞口被画着人像的布帘封住…雷雨导致遮挡物脱落 | 0.12 (0 + 12) |
| 30 | 是因为积水使主角身体位置升高吗？ | 不是 | 两个被纸糊住的窗户洞口…雷雨导致纸张脱落 | 0.12 (0 + 12) |

Three things the table shows that no mean curve can. **The checkpoint mechanism surfaces knowledge the agent never acts on:** the round-10 committed story *is* the solution — synthesized from earlier answers, on a round whose own question was answered 不是 — yet the model never volunteers a final answer in all thirty rounds (it is one of the 57/66 non-committing 397B games), and by round 19 it has abandoned the correct reading for a falling-coverings mechanism it never escapes. **Stalling in fresh words happens at the largest scale too:** rounds 22–30 are eight lexically distinct re-asks of the same flooding hypothesis, exactly the pattern lexical novelty misses (§6). **And the curve's round-to-round jitter is a scoring fact, not a knowledge fact:** the same understanding re-worded (rounds 3 → 4) swings the clue half 70 → 0; the mean curves of §5.1 average this out, which is why single-game curves are not the unit of analysis.

---

## Open questions for the authors (feedback wanted before v1.0)

*(Resolved: v0.1 decisions 2 & 5 — grid ran, Figure 1 real. v0.2 decisions 1 & 5 — abstract/intro now lead with flatness; mixed-effects ran: H3 not supported within-puzzle, so the paper claims geometry as interpretive, not predictive. v0.9: flatness-first hook confirmed by the author on the new grid; Q1 below answered empirically — under-determination is not significant (p = 0.22) and absorbs ~8% of the puzzle variance, so the softened H3 framing stays, now with the covariate test to cite.)*
1. **H1 on the new grid:** stalling now shows as the small model's *low and shrinking* stride (0.049 mean, 0.030 late) rather than a sign inversion — H1 reads cleaner than on the old grid. Any objection to stating H1's confirmation in exactly those terms in the intro?
2. **Human data (still open):** the manifold remains the documented proxy. SWOW-zh sourcing or a small human-trace collection would strengthen H2's between-puzzle claim. Feasible before the deadline?
3. **Title (still open):** "Thinking Sideways, Observed" — alternatives welcome.
4. ~~**Length check**~~ — resolved 2026-09-04: trim pass done (§2 condensed, intro/limitations/conclusion tightened, figures resized); main text ends exactly at page 4, references + appendices follow.
