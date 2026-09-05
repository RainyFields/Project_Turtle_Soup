# Thinking Sideways, Observed: Interpreting the Lateral-Thinking Search Behavior of LLM Agents with Turtle Soup Puzzles

**Target venue:** IAB — Interpreting Agent Behavior, Workshop @ NeurIPS 2026 (https://iab-agents.github.io/)
**Draft:** v0.16-A — 2026-09-05 — **re-spined around a single mechanism.** v0.13 was organized around results: flatness, then budget, then two patterns, then nulls, with the Oracle audit standing as a co-equal second thesis. True, but not one line. The spine is now: **the Oracle's answer barely changes what the agent does next, and where it does, it pushes the wrong way** — one fact from which the flat curve, both failure patterns, and both null results follow. The audit material becomes a validity condition (one sentence in the body, protocol in Appendix B) rather than a contribution: with a 95% cross-family Oracle it is no longer a live problem for these results. New measurements behind the spine (`scripts/feedback_response.py`, `scripts/underdet_vs_behaviour.py`): feedback response by tier, the round-1 prior, and the sub-semantic character of abandoning. Previous versions in `git log`.

**Status:** v0.13 compiled and page-checked (8-page PDF, main text ends exactly at page 4). Draft synced to it 2026-09-05. See "Open questions for the authors" at the end.

---

## Abstract

**Page budget: ~0.25 page.**

An interactive agent is supposed to use what it is told. We instrument Turtle Soup, a lateral-thinking game of yes/no questions, with two process-level probes — a forced and scored checkpoint story every round, and an association trajectory embedded from each round's question — and run three Qwen tiers on 22 human-played puzzles. Accuracy is flat after round ten at every tier, and the round budget is not the constraint. The reason is visible in the process: **the Oracle's answer barely changes what the agent does next.** Controlling for round position, the smallest tier's next move is statistically independent of whether it was just confirmed or refuted (Δ stride +0.001, 95% CI [−0.009, +0.011]); the larger tiers do respond, but backwards, moving *further* after a confirmation than after a refutation (+0.028 [+0.010, +0.046] and +0.009 [+0.002, +0.017]) — the opposite of a search that eliminates hypotheses. The two failure patterns follow. Unable to be pushed out of its first basin, the small model **circles** (late-game stride 0.030 vs 0.082). Free to settle next to a confirmed neighbour, the largest tier **abandons**: it reaches the solution in 6 games and commits 1, and the story it ends with sits no further from the one that scored 1.00 than any two rounds of the same game sit from each other (0.851 vs 0.841). That last number is why the geometry describes these failures without predicting scores: losing a correct answer is a sub-semantic event. One endpoint number scores all of this identically. We release the harness, both instruments, the puzzle set, and every per-game log.

## 1. Introduction

**Page budget: ~1.0 page, including Figure 1.** Version A: the figure carries the hook. The reader meets the phenomenon before any terminology, and the three hypotheses are posed against something they can already see.

- **The puzzle, first.** A man's body lies in the desert, clutching half a matchstick; luggage and clothing are scattered around him. That is all the solver sees. The hidden story: a hot-air balloon was losing altitude; the passengers threw out their luggage, still could not stay up, and drew lots with matchsticks; the man who drew the short one was thrown out. The solver recovers this story by asking yes/no questions, one round at a time — and an agent doing so leaves its entire search in plain text.

**[FIGURE 1 HERE]** — (a) accuracy of the answer each tier would give at each round, full 0–1 axis, with rounds 1–14 magnified; (b) the best answer each game reached against the answer it finally stands on.

- **What the figure shows.** Interaction helps, and then stops helping: gains arrive in the first ten of thirty rounds and nowhere after. And the answer each agent finally stands on sits below the best one it had already produced — by 0.034, 0.075 and 0.106 across the three tiers, which is the same 24–31% of what was reached at every scale. **Capability buys a higher peak and loses the same share of it.**
- **Three explanations, and why they are the right ones to test.** Each is what a reader would reach for first, and each makes a prediction the trajectory instrument can check.
  - **H1.** The search narrows in on the answer as 不是 answers eliminate hypotheses. *Predicts:* stride shrinks, and shrinking stride means closing in.
  - **H2.** The answer redirects the next question — a refutation should push the search away, a confirmation should refine it. *Predicts:* larger strides after 不是 than after 是.
  - **H3.** When the agent reaches the answer it will stop. *Predicts:* the game ends at its peak — the agent volunteers there, and the answer it finally stands on is the best one it produced.
- **What we find.** H1 half-holds and misleads: the search narrows four to five fold and converges on nothing. H2 is refuted with the sign reversed — the smallest tier's next move is independent of the answer, the larger two move *further* after a confirmation. H3 is refuted at the point that matters: 397B reaches a solution-grade answer in six games and volunteers one. And the reason it does not stop is measurable — the move that leaves the answer behind is the same semantic size as any ordinary step, so nothing marks the moment it should have halted.
- **Contributions.** (1) A measurement of **feedback response** in an interactive agent, with round position controlled. (2) Two failure patterns derived from it rather than catalogued, **circling** and **abandoning**, with per-game criteria and counts. (3) An honest boundary on the instrument, with the reason it holds. (4) Released harness, both instruments, a 22-puzzle human-played set, and every per-game log.

**Not here:** related-work detail (§2), method detail (§3). **Conditions of validity** are one sentence in §5 and a protocol in Appendix B.

## 2. Related Work

**Page budget: ~0.3 page.** The first section to compress when space is short.

Existing turtle-soup benchmarks — TurtleBench [1], SPLAT [2] (whose interactive player–judge protocol we adopt), and TurtleSoup-Bench [3] — score verification accuracy, solve efficiency, or faithfulness to the intended story. TurtleSoup-Bench probes what agents ask next but grades it against the intended story; **none of the three measures the search's geometry, which is our delta.** Circling and abandoning echo folk-known multi-turn failure modes (repetitive questioning; failing to commit or retain a correct answer) — our contribution is to *measure* them, not to claim their novelty. MUTATE [4] shows frontier agents find far fewer mechanism-distinct paths than humans; its diverge-then-narrow agent is a natural test intervention for our metrics. The instrument itself adapts forward flow [7] and the Divergent Association Task [8] from human psychometrics. The Small World of Words norms [9] provide the human anchor that ours is not yet (§3.5). Judge-bias catalogues [5, 6] shape the scoring: the model judge is confined to the one subscore that objective matching cannot reach.

*(Cut for space, recoverable from git: CreativityPrism and reference-based creativity scoring as the novelty × appropriateness consensus behind the composite; Chen & Ding on divergent semantic association in LLMs.)*

## 3. Framework

**Page budget: ~0.9 page.** Five subsections, one paragraph each. v0.13 promoted the checkpoint protocol to its own subsection: it is an *instrument*, not a scoring detail, and burying it made the accuracy curve unreadable.

### 3.1 Task and harness

A Questioner sees only the 汤面 (the "surface", the puzzle's visible scenario) and asks one yes/no question per round. An Oracle holds the 汤底 (the hidden story) and answers 是/不是/与此无关 (yes, no, or irrelevant). The Questioner may commit a final story at any round, or is forced to at the budget. The open-source harness has pluggable model providers and logs every round, with per-game seeds.

### 3.2 Checkpoint and commitment instrumentation

**Our first instrument does not wait for the end.** Every round, after the Oracle answers, the Questioner must write its best complete story, and that checkpoint is scored; each point on an accuracy curve is therefore a full answer written with the evidence available at that round. Alongside it we record **commitment**: whether and when the agent ever volunteers a final story of its own accord. Together these turn an endpoint benchmark into a scored process.

### 3.3 Puzzles

Conclusions only; the provenance audit belongs in Appendix A. A puzzle nobody has solved carries no evidence that its clues suffice, that its solution is unique, or that the intended leap is reachable; an agent scoring zero on it teaches us nothing. Our set therefore takes only puzzles with a public record of human play: **22 items** from a Chinese Turtle Soup community site, each keeping its source URL. Surfaces run 9–108 characters (median 34), solutions 13–200 (median 102), with 97 annotated key clues. Provenance is enforced in code, with a verified family, a quarantined generated family, and tests that fail if the two mix.

Each puzzle carries an **under-determination** score: how far the surface alone leaves a solver from the solution, measured by taking the closest of twelve cold guesses written from the surface with no Oracle feedback. It ranges 0.173–0.577 (median 0.347) and is not explained by surface length within this small set (r = −0.22, n.s., n = 22). It enters the mixed-effects analysis in §5 as a puzzle-level covariate.

### 3.4 Outcome scoring: composite, not surface

Judged outcome is **clue recall (70)** plus **causal-logic identity (30)**; Appendix B gives the detail. String matching alone cannot tell a wrong answer from a right one worded differently: we watched a frontier model reconstruct a hidden causal chain completely and score 0.00. Conversely, the clue half blocks "far = creative" gaming, because distance without validity scores zero.

### 3.5 Association-trajectory instrumentation

The second instrument reads the questions themselves. Each round we extract the question's keywords (jieba), embed them (bge-small-zh-v1.5), and average them to a unit round vector *q_t*; distances are cosine, and anchors embed the puzzle's surface, solution, and clue terms (specification in Appendix B). Two signals follow: the **stride** *s_t = d(q_t, q_{t−1})* and the **anchor distance** *h_t = d(q_t, A)*, with Q1's signature *s̄ → 0* and Q2's a rising *h_t*; the lexical `question_novelty` metric is the ablation baseline that Q1 predicts will miss synonym drift.

**One caveat up front, and it must stay in the body — it bears on Q2's credibility.** The anchor is a stated proxy, not a human association manifold; its consequences are quantified with the results (§5), and a SWOW-based version [9] is the correct future form.

## 4. Experiment Designs

**Page budget: ~0.3 page.** Down from ~0.4: the Oracle audit no longer gets its own paragraph here.

**Designs.** **E1** (round curve) plays to 30 rounds under the checkpoint instrument (§3.2), and supplies every trajectory analysed in §5. **E2** (round budget) imposes hard caps {5, 10, 15, 20, 25, 30} with a forced final answer only, so it doubles as a **no-checkpoint control**. **E3** computes {*s_t*} and {*h_t*} for every E1 game, and joins each round's stride to the answer received the round before — the join that makes feedback response measurable. The keyword extractor is fixed across models, so none is scored through its own vocabulary.

**Feedback response, defined.** For each round *t* we pair the Oracle's answer (是 / 不是 / 与此无关) with *s_{t+1}*, the stride into the following question. A searcher that eliminates hypotheses should move *further* after 不是 than after 是. Confirmation arrives earlier in a game than refutation (mean round ~10 vs ~16) and early strides are larger, so the comparison is made **inside (puzzle, round-bin) cells**; CIs bootstrap over puzzles. Without that control the effect is manufactured at every tier — the uncontrolled and controlled estimates are both reported in Appendix B.

## 5. Results

**Page budget: ~1.5 pages, including Figures 1–2.**

All numbers come from one grid on the verified set: 22 puzzles × {Qwen3.5-4B, Qwen3.6-27B, Qwen3.5-397B-A17B; hereafter **4B, 27B, 397B**} × 3 seeds. **Conditions of validity, in one sentence:** the Oracle and logic judge are DeepSeek-V3.1, cross-family with the Questioners and audited at 95% on held-out probes, and one environment artifact (token exhaustion at the smallest tier) is removed in §5.1 before any behavioural comparison — protocol and settings in Appendix B. Accuracy denotes the composite score rescaled to [0, 1]. E1 comprises **198** thirty-round games with a scored checkpoint every round; E2, **1,188** games across caps.

### 5.1 The phenomenon, and what it is not

*(Figure 1 is in §1; this section supplies the numbers behind it and rules out two explanations.)*

Interaction does help — for ten rounds. 397B climbs 0.124 → 0.200 by round 10, 27B 0.117 → 0.162; 4B is flat throughout at 0.05–0.06. Then it stops: the round 10 → 30 change is −0.009 / +0.003 / −0.013, with puzzle-clustered CIs spanning zero.

**And the answer the agent finally stands on sits below the best one it reached.** Against its own sustained peak (the best score held over two consecutive checkpoints), each tier ends lower: −0.034 / −0.075 / −0.106. The absolute gap grows with tier because the peak does; **as a fraction of what was reached it is the same everywhere** (24% / 31% / 27%). Scale buys a higher peak and loses the same share of it.

**It is not the budget.** E2's end accuracy is insensitive to the round cap for the larger tiers (397B 0.19–0.21, 27B 0.14–0.18 across all six caps). The smallest model's raw curve declines monotonically (0.050 → 0.004), but that is the environment: token-exhausted games rise from 0/66 at cap 5 to 63/66 at cap 30, and conditioned on non-exhausted games 4B does not decline (0.05–0.09).

**It is not a degenerate Oracle.** The Oracle is audited at 95% and its replies are informative: 68–74% 不是, 14–24% 是, with 与此无关 at 7.4% and 7.7% for the larger tiers.

**It is not the puzzles either.** Under-determination — how far the surface alone leaves a solver from the solution (§3.3) — predicts what a model writes before any evidence arrives (ρ = −0.34 / −0.54 / −0.47 against the round-1 checkpoint) and nothing after it. It does not predict the round 10 → 30 change, any trajectory indicator, either half of the score, or the gap between tiers (all n.s.; Appendix B). **Difficulty separates puzzles, not models, and stops mattering once the first question is asked.** With 22 puzzles these are bounds rather than absences: an effect smaller than about ρ = 0.4 would not be detected here.

So the evidence is there, the budget is there, the puzzles are within reach, and the agent stops making progress anyway. The next three subsections take the three explanations a reader would reach for first, and test each.

### 5.2 H1 — "the search narrows in on the answer" — it narrows, it does not converge

The intuition is that accumulated 不是 answers eliminate hypotheses, so the search should contract around what survives. **The contraction is real.** Mean stride falls monotonically at every tier, by four to five fold: 4B 0.145 → 0.025, 27B 0.232 → 0.053, 397B 0.182 → 0.045 from round 1 to round 29.

**The convergence is not.** Accuracy over those same rounds is flat (§5.1), and within a tier stride does not predict how well a game ends (|ρ| ≤ 0.16; mixed-effects coefficients bounded within ±0.035 per SD, Appendix B). The narrowest searcher of all, 4B at a late-game stride of 0.030 [0.021, 0.039] against 27B's 0.082 [0.065, 0.098], is the one that never reaches a solution-grade answer at all. **Narrowing is what circling looks like from outside** — orbits of one hypothesis basin, tightening around nothing. Not a malformed-question artifact: 17% of 4B's questions are truncated or non-interrogative (~1% elsewhere), yet excluding them barely moves either statistic (0.049 → 0.056; 0.030 → 0.033).

### 5.3 H2 — "the answer redirects the next question" — it barely does, and backwards

If the search narrows without converging, perhaps it is narrowing on the wrong thing. That would still require the answers to steer it. **They barely do.** Pairing each answer with the stride into the following question, inside (puzzle, round-bin) cells so that the earlier arrival of 是 cannot manufacture the effect (Figure 2a):

| tier | Δ stride (after 是 − after 不是) | 95% CI | reading |
|---|---|---|---|
| 4B | **+0.001** | [−0.009, +0.011] | no detected response |
| 27B | **+0.028** | [+0.010, +0.046] | responds, inverted |
| 397B | **+0.009** | [+0.002, +0.017] | responds, inverted |

A refutation eliminates a hypothesis and should force a jump; a confirmation narrows the space and should invite a refinement. **The smallest tier's next move is statistically independent of the answer it just received** — nothing in the feedback channel can push it out of the hypothesis it started with. **The larger two do respond, with the sign reversed**, treating 是 as licence to move on and 不是 as reason to stay. Since 68–74% of answers are 不是, most rounds are spent not moving.

### 5.4 H3 — "when it finds the answer it will stop" — it does not stop

The remaining explanation is that the agent reaches the answer and simply runs out of rounds before it can act on it. It does not: it reaches the answer, keeps going, and lets it go.

**Found, and not volunteered.** Call a sustained peak ≥ 0.5 (half the scale) **solution-grade**. 4B reaches none; 27B reaches four and volunteers three; **397B reaches six and volunteers one**, ending four of them below half peak (Figure 2b). Commitment is rare everywhere — 11/66, 9/66, 2/66 games — and late when it happens (mean round 11.1, 14.2, 23.5).

**And when it does volunteer, it often volunteers less than it had.** Of the 22 volunteered games, several submit a story well below the best that game had already produced: 27B commits 0.075 on a game whose peak was 0.542, and 0.015 on one that peaked at 0.263; 397B commits 0.650 where it had reached 0.883. This is a chosen answer, not a forced one.

**Why it does not stop.** In abandoning games the final story sits at cosine 0.851 from the peak story that scored up to 1.00 — while any two checkpoints of the same game sit at 0.841, and two stories from different puzzles at 0.498 (Figure 2c). **The move that loses the answer is the same semantic size as ordinary within-game motion**, though the score falls by 0.30. There is no signal on which to halt, and neither the agent nor the geometry has one: this is why trajectory features describe these failures without predicting scores, and why the drift signature of a wandering search never appears (slopes cluster near zero at every tier). A fatal substitution smaller than the encoder's resolution cannot be predicted from that encoder.

**Both anchors, as promised (§3.5).** Slopes from the solution-aware and surface-only anchors agree in rank (ρ = 0.80) and the conclusion is unchanged under either (Appendix B).

## 6. Limitations and Conclusion

**Page budget: ~0.35 page.**

**Limitations.** The feedback measurement reads *how far* the next question moves, not *what* it asks; a model could in principle relocate appropriately while striding identically, and a content-level test of feedback use is the natural next study. Round position is controlled by binning, which is coarse. Truncated chain-of-thought under a tight token budget masquerades as an agent that cannot form a question (§5.1); decoding is part of the environment, and the Oracle's ~95% audited accuracy implies roughly one wrong answer per 30-round game, an unmeasured environment term. The anchor is not yet human-derived (§3.5), so the geometry is a stated proxy. Keyword extraction and encoders are themselves models — and §5.3 shows the encoder's resolution is itself a limit on what any embedding-based instrument can score. One DeepSeek model serves as both Oracle and judge (cross-family judge check pending), and the tiers confound generation and architecture, so tier effects are **model comparisons, not scaling laws**. The source site is public and memorisation probes are pending; nothing rests on the n.s. under-determination covariate. Puzzles involve death and dark themes; content-flagged.

**Conclusion.** The flat curve is not a budget limit or a capability ceiling; it is what happens when evidence does not move the search. One tier cannot be moved by the answer at all and circles; two are moved the wrong way, settling next to a confirmed neighbour of the truth and abandoning it. The two need opposite interventions — one needs to be dislodged, the other needs to be made to commit — and a single endpoint number scores them identically. **Reading agent behavior here required instrumenting the channel the agent was supposed to be learning from.**

## References

**Numbering matches the tex** (9 cited). Three earlier entries were cut for space in v0.13 and are listed after.

1. Yu, Song, Fang, Shi, Zheng, Wang, Niu, Li. *TurtleBench: Evaluating Top Language Models via Real-World Yes/No Puzzles.* arXiv:2410.05262
2. Chen, Zhang, Wang, Wu. *Weak-eval-Strong: Evaluating and Eliciting Lateral Thinking of LLMs with Situation Puzzles (SPLAT).* arXiv:2410.06733
3. Zhou, Wu, Zhang, Sima, Liu. *What to Ask Next? Probing the Imaginative Reasoning of LLMs with TurtleSoup Puzzles.* arXiv:2508.10358
4. Park, Baek, Park, Lee. *Beyond One Path: Evaluating and Enhancing Divergent Thinking in Interactive LLM Agents (MUTATE).* arXiv:2605.28465
5. Ye et al. *Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge (CALM).* ICLR 2025; arXiv:2410.02736
6. Shi, Ma, Liang, Diao, Ma, Vosoughi. *Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge.* IJCNLP-AACL 2025
7. Gray et al. *"Forward Flow": A New Measure to Quantify Free Thought and Predict Creativity.* American Psychologist 74(5), 2019
8. Olson, Nahas, Chmoulevitch, Cropper, Webb. *Naming Unrelated Words Predicts Creativity (DAT).* PNAS 118(25), 2021
9. De Deyne, Navarro, Perfors, Brysbaert, Storms. *The "Small World of Words" English Word Association Norms.* Behavior Research Methods 51(3), 2019

*Cut for space in v0.13 (restore if a page frees up):* CreativityPrism (arXiv:2510.20091); Li et al., reference-based creativity scoring (arXiv:2504.15784); Chen & Ding, divergent semantic association in LLMs (arXiv:2310.11158).

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

Two properties make this usable as a covariate. It describes the puzzle, not any agent's performance on it. And it is independent of rounds used — a difficulty defined as "how many rounds this takes" would make an accuracy-versus-rounds plot confirm itself. Nor is it a proxy for surface length (r = −0.22, n.s.), so length dependence **was not detected at n = 22 — a weak test**, not a demonstration of independence. It is one measure rather than two: a surface loose enough to admit many mechanisms is, for that same reason, one whose true mechanism takes more reframing to reach, so *how far* and *how many ways* are not separable here.

**A caveat we report either way.** The two puzzles scoring easiest are the two most widely circulated ones. Their surfaces may be easy to complete not because the inference is short but because the story is in the training data, in which case the measure reads familiarity as much as difficulty. A memorisation probe — asking for the solution with no surface given — separates the two and belongs in any use of this measure.

---

## Appendix B — Measuring agent performance

**No page limit.** v0.13 moved the LMM coefficients, the retention estimator, the permutation spec and the judge scale here to buy main-text space.

**What counts as a correct answer.** Judged outcome is **clue recall (70)** plus **causal-logic identity (30)**. Clue recall matches the answer against per-puzzle annotated key clues: objective and reproducible. The logic judge rates only whether cause → mechanism → outcome matches and is told explicitly to ignore wording. Because single ratings are unstable on borderline answers, ratings are sampled and averaged (**two samples per rating in the reported grid**). The gap between the two subscores is itself readable: right story, wrong vocabulary.

Clue matching tolerates paraphrase through character-bigram recall, which sets a floor on how short an annotated clue may be. Below that floor only a verbatim match counts, and the score reads vocabulary rather than content. Clues are annotated above the floor.

**What the two halves measure, and why they are separate.** Clue recall is objective and reproducible but literal: it can only credit content that appears, in words close enough to match. Causal-logic identity is the opposite — the judge is told to ignore wording and rate only whether cause → mechanism → outcome corresponds — but it needs a model, so it is confined to the one subscore objective matching cannot reach. The pair is informative because the two do come apart: models earn a several-fold larger share of the logic half than of the clue half (397B 12.6/30 against 7.2/70, 27B 10.1 against 6.8, 4B 2.9 against 0.2), the halves correlate only weakly per game (Spearman ρ = 0.30 / 0.35 / 0.06 for 397B / 27B / 4B), and **the gap holds in all nine tier × difficulty-band cells** (logic rate 1.3–4.8× the clue rate), so it is a property of the scoring rather than of easy puzzles. The 70/30 weighting is a design choice: every conclusion in §5 is readable from the halves separately, though the absolute plateau level (~0.2) depends on the weights. The logic judge is sampled twice per rating at temperature 0.2; the two samples agree exactly in 86% of ratings.

**Feedback response: definition, confound, and both estimates.** For each round *t*, the Oracle's answer is paired with *s_{t+1}*, the stride into the next question; 与此无关 rounds are excluded. Confirmation arrives earlier than refutation (mean round 12.1 / 9.7 / 10.9 for 是 against 15.6 / 15.6 / 15.9 for 不是) and early strides are larger, so an uncontrolled comparison is confounded by position. Pairs are therefore formed inside (puzzle, round-bin) cells with bins {1–5, 6–10, 11–15, 16–20, 21–25, 26–29}, and 95% CIs bootstrap over puzzles (4,000 resamples). Both estimates, since the gap between them is the point:

| tier | uncontrolled Δ | controlled Δ |
|---|---|---|
| 4B | +0.024 [+0.004, +0.044] | **+0.001 [−0.009, +0.011]** |
| 27B | +0.043 [+0.015, +0.070] | **+0.028 [+0.010, +0.046]** |
| 397B | +0.034 [+0.023, +0.046] | **+0.009 [+0.002, +0.017]** |

Uncontrolled, all three tiers appear to respond; controlled, the smallest does not. `scripts/feedback_response.py` → `figures/feedback_response.json`.

**The semantic scale of abandoning.** Within abandoning games (sustained peak ≥ 0.3, final below half of it; n = 34), the final checkpoint story sits at cosine 0.851 (median) from the peak story, while any two checkpoints of the same game sit at 0.841 (median over all 77,906 within-game pairs from 60 games) and two stories from different puzzles at 0.498 (231 pairs) — all under the encoder of §3.5. The score gap across that same pair is 0.447 → 0.099.

**The round-1 prior.** The round-1 checkpoint precedes the first Oracle answer and is therefore a cold guess. It holds 49% / 33% / 26% (median, by tier) of the game's eventual best score, and correlates with it at ρ = +0.37 / +0.57 / +0.47 (permutation p = 0.09 / 0.003 / 0.03, n = 22 puzzles with seeds averaged). Under-determination — itself measured from twelve cold guesses by GLM-5.3-flash, cross-family with every Questioner — predicts round-1 quality at ρ = −0.34 / −0.54 / −0.47 (p = 0.12 / 0.010 / 0.029) but not the final score. `scripts/underdet_vs_behaviour.py`.

**Puzzle structure against behaviour and against the subscores.** Regressing each per-trace indicator on under-determination (seeds averaged, 5,000 permutations): stride, late stride, drift under both anchors, mean anchor distance and rounds played are n.s. at every tier (|ρ| ≤ 0.32, p > 0.10). The two subscores behave the same way — neither the clue half, the logic half, nor the balance between them varies with under-determination (1 of 9 tests reaches p < 0.05, against a chance expectation of 0.45), so difficulty does not change the *kind* of failure, only which puzzles start close to the answer. Commit rate is negative at all three tiers (−0.32 / −0.25 / −0.43) but pooled p = 0.13, and 1 of 24 tests reaching p < 0.05 is again the chance expectation, so we report it as unresolved. `scripts/underdet_vs_behaviour.py`.

**Retention estimator and permutation null.** Retention is the mean per-game final-to-sustained-peak ratio over games with a nonzero sustained peak; the final is the last played checkpoint, and excluding early-committing games changes each tier's value by ≤ 0.03 (bootstrap 95% CIs ±≈0.08). For the null: unit, the game. For each of 2,000 permutations, every game's checkpoint sequence is shuffled within the game (knowledge-constant, jitter-only null), the sustained peak and the final (last element) are recomputed on the shuffled sequence, and retention is the mean over that tier's games with a nonzero permuted peak. The reported *p* is one-sided per tier: the fraction of permutations whose null retention is at or below the observed value. Late-game stride means the second half of a game's strides.

**Mixed-model coefficients.** Best checkpoint accuracy per game; Gaussian LMM, puzzle random intercept, tier fixed effect, ML fits, likelihood-ratio tests against the covariate-only model. Stride β = −0.010 per SD, 95% CI [−0.035, 0.014], p = 0.42; drift β = −0.011, [−0.035, 0.014], p = 0.39; stride × tier p = 0.20; surface-anchor drift β = −0.020, [−0.044, 0.003], p = 0.097.

**Environment settings and Oracle audit.** Every model call uses `max_tokens` 2048 (thinking disabled, temperature 0.2) with a per-game budget of 50,000 tokens; exhausting it forces a final answer and is recorded as the outcome `token_budget`. The audit probes a candidate with 25 hand-crafted (question, expected-answer) pairs over three puzzles — 21 with a definite yes/no answer and 4 expecting "irrelevant" — with a 90% pass bar on the yes/no items. The deployed DeepSeek-V3.1 scored **20/21 (95%)** on the yes/no items and 3/4 exact on "irrelevant", and comes from a different model family than every Questioner.

**Trajectory and difficulty pipeline.** Keywords are extracted with jieba after stripping Latin characters and digits; each keyword is embedded with bge-small-zh-v1.5 (normalized), and the round vector is the re-normalized mean of its keyword embeddings. All distances are cosine. The **solution-aware anchor** embeds the puzzle's surface, solution, and clue terms; the **surface-only anchor** embeds surface terms alone. The under-determination measure prompts GLM-5.3-flash (cross-family with all Questioners) for twelve cold guesses from the surface and scores closeness as embedding similarity between guess and solution under the same encoder — **not with the composite score**, so the covariate is not coupled to the outcome apparatus.

**Artifacts.** Harness, puzzle set with per-item source records, per-game logs (including every checkpoint story), and the analysis scripts behind each reported number are released at `github.com/RainyFields/Project_Turtle_Soup`. Puzzle surfaces and solutions originate from a public community repertoire and are redistributed with source attribution and a content flag.

**One game, worked.** Puzzle `refsoup_021` — surface: a stormy night, a run-down temple, two photographs on the wall that seem to stare; by morning the narrator sees only two windows. Solution: 墙上根本没有照片，是有人贴着窗户往里看 ("there were never photos on the wall; people were pressing against the windows, looking in"). Played by Qwen3.5-397B, seed 2. **Seven** of thirty rounds; Chinese cells verbatim from the log with our translations, stories abridged to the clause carrying the hypothesis. Rounds 22–30 — eight lexically distinct re-asks of the same flooding hypothesis (e.g. round 25, whether the narrator woke floating upside down; round 28, whether rising water reached eye level) — are in the released logs.

| 轮 | Question (abridged) | 答 | Committed story (abridged) | score (clue + logic) |
|---|---|---|---|---|
| 1 | 照片里的是人吗？ *Are the figures in the photos people?* | 是 *yes* | 那两张"照片"…是两个被钉死或封在墙洞里的人 | 0.12 (0 + 12) |
| 3 | 主角第二天醒来时，还在那座寺庙里吗？ *Is the narrator still in the temple on waking?* | 是 *yes* | 所谓的"两张照片"其实是两扇窗户…昏暗光线下…误看成了照片 | 0.91 (70 + 21) |
| 4 | 醒来看到的"两扇窗户"就是昨晚的"两张照片"吗？ *Are the "two windows" the same objects as last night's "photos"?* | 是 *yes* | "照片"实际上是两个被挖空的人形窗口…恐惧感源于黑夜和错觉 | 0.12 (0 + 12) |
| 10 | "两扇窗户"是因为相框玻璃破碎脱落吗？ *Did frame glass break and fall, leaving open holes?* | 不是 *no* | 那根本不是照片，而是…贴在窗玻璃外侧的人脸 | **1.00 (70 + 30)** |
| 11 | 是因为照片被取走、露出了后面的窗户吗？ *Were the photos removed, revealing windows behind?* | 不是 *no* | 昨晚"盯着他的人像"，其实是**窗外的人** | **1.00 (70 + 30)** |
| 19 | 照片里的人像实际上是躲在照片后面的真人吗？ *Were real people hiding behind the photos?* | 不是 *no* | 窗户洞口被画着人像的布帘封住…雷雨导致遮挡物脱落 | 0.12 (0 + 12) |
| 30 | 是因为积水使主角身体位置升高吗？ *Did rising water raise the narrator's position?* | 不是 *no* | 两个被纸糊住的窗户洞口…雷雨导致纸张脱落 | 0.12 (0 + 12) |

*Glosses:* 汤面 = the visible surface scenario; 汤底 = the hidden story; 是/不是 = yes/no; 与此无关 = irrelevant.

**Three things the table shows that no mean curve can.**

1. **The checkpoint mechanism surfaces knowledge the agent never acts on.** The round-10 committed story *is* the solution — synthesized from earlier answers, on a round whose own question was answered 不是 — yet the model never volunteers a final answer in all thirty rounds (one of the 57/66 non-committing 397B games), and by round 19 it has abandoned the correct reading for a falling-coverings mechanism it never escapes.
2. ---

## Open questions for the authors

*Resolved and no longer open:* the grid ran (Figures real); H1–H3 became Q1–Q3 with verdicts stated in §1; H3/predictivity settled as not-supported, so the paper claims the geometry as interpretive; the under-determination covariate was tested and is n.s. (p = 0.22, ~8% of puzzle variance); the retention claim was withdrawn under a permutation null; the 4B budget decline was reattributed to the harness; length resolved (main text ends exactly at page 4).

1. **Human data (open).** The anchor remains the documented proxy. SWOW-zh sourcing or a small human-trace collection would strengthen Q2. Not feasible before this deadline; flag as future work?
2. **Memorisation probe (open, cheap).** ~22 calls, asking for each solution with no surface given. It converts Appendix A's caveat from "should be done" into a measured statement, and Limitations currently says probes are *pending*. Worth doing before submission?
3. **Title (open).** "Thinking Sideways, Observed" — alternatives welcome.
4. **Under-determination × behaviour (new, 2026-09-05; see `temp_plan.md`).** Behavioural indicators were regressed on under-determination. Geometry is flat (all |ρ| ≤ 0.32, p > 0.10); only commit rate moves, consistently negative at all three tiers (−0.32 / −0.25 / −0.43) with a tercile drop 0.25 → 0.05 while accuracy does not fall. Pooled p = 0.12, and 1 of 24 tests reaching p < 0.05 is the chance expectation — **so this is not a finding.** Decision needed: (A) two sentences in §5.3 with an equal cut elsewhere, (B) Appendix A only, (C) leave out. Current lean: **B**.


---

## Figures (for tex generation)

| # | file | panels | serves |
|---|---|---|---|
| 1 | `fig1_flatness` | (a) checkpoint accuracy by round, full 0–1 axis, round-10 rule, early-rise inset; (b) final vs sustained peak, commitment-coded markers | §5.1 — the flat curve, and abandoning's first evidence |
| **2** | **`fig_feedback` (new, v0.15)** | **(a) Δ stride after 是 minus after 不是, per tier, dot + 95% CI, zero rule; (b) violin: peak→final in abandoning games vs any two rounds of one game vs two puzzles** | **§5.2 — the central measurement; §5.3 — why the geometry cannot score it** |
| 3 | `fig2_geometry` (was Figure 2) | (a) per-tier stride strips; (b) drift slope vs best accuracy | §5.2 circling signature; §5.3 Q2 rejected |
| 4 | `fig3_worked_game` | one abandoning game's checkpoint scores by round | Appendix B worked example |

**Style** follows `make_figures.py`: 7 pt Arial, no top/right spines, `#9DB8D9 / #4C7BB8 / #173A66` by tier with `#C0504D` reserved for reference rules, 5.2 × 1.75 in, PDF + PNG at 400 dpi. `make_feedback_figure.py` runs the nature-figure alignment audit when that skill is installed and skips it with a printed note otherwise — **run it on a machine with the skill before submitting**, so Figure 2 gets the same audit as Figures 1 and 3.

⚠️ **Figure count rises from 3 to 4.** Main text is currently 19,462 characters against v0.13's 19,633 at exactly 4 pages, so prose has room, but a fourth figure does not fit for free. Options: retire Figure 3 to the appendix (its stride panel is now redundant with §5.2's table, and its drift panel supports a rejected hypothesis), or place Figure 2 as a single-column half-width figure.
