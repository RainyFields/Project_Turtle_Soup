# Thinking Sideways, Observed: Interpreting the Lateral-Thinking Search Behavior of LLM Agents with Turtle Soup Puzzles

**Target venue:** IAB — Interpreting Agent Behavior, Workshop @ NeurIPS 2026 (https://iab-agents.github.io/)
**Draft:** v0.8 — 2026-08-30 — rewritten for readability on the v0.3 structure; dataset section added (22 human-played puzzles); appendix drafted. PDF at `docs/paper/iab2026.pdf`; structure spec at `docs/paper/paper-outline.md`.
**Status:** awaiting author feedback; see "Open questions for the authors" at the end.

---

## Abstract

> ⚠️ **待填 —— 依赖重跑。**下列数字全部来自已作废的旧题集，已删除。
> 重跑后按此结构回填：
>
> 1. **主结果（一句）**：更多交互是否提升准确率？给出各模型的平坦性与预算效应。
> 2. **两种失败模式（本文核心）**：同为 0 分但行为相反 —— 原地打转（后期步长趋近 0、
>    从不提交）vs 探索但不沉淀（步长大、覆盖广、却不转化为更好的假设）。
>    **需要两个具体数字撑起对比。**
> 3. **诚实的否定**：轨迹几何在题目内是否有预测力（混合效应）。
> 4. **锚点的实话**：锚点含汤底信息，两个锚点下结论是否一致。
> 5. **方法论提示**：弱 Oracle 会让任务在信息论意义上无解。

## 1. Introduction

**Page budget: ~0.9 page.**

- **Open with a puzzle.** *A man's body lies in the desert, clutching half a matchstick; luggage and clothing are scattered around him.* That is all the solver sees. The hidden story: a hot-air balloon was losing altitude, the passengers threw out their luggage and were still too heavy, so they drew lots with matchsticks — and the man who drew the short one was thrown out. The solver recovers this by asking yes/no questions, one per round. **Keep this. A reader who has not seen a Turtle Soup puzzle cannot follow anything that comes after.**
- **Hook.** ⚠️ *Pending re-run.* The intended shape: give an agent thirty rounds and it does not get better as the dialogue grows. Outcome metrics can state that flatness but cannot explain it — two agents scoring 0.0 may be failing in opposite ways, one never leaving its first hypothesis, the other leaving the plausible region entirely. Explaining it needs instruments that read the *process*, which is this paper's contribution. **If the re-run does not reproduce the flatness, the hook becomes the failure-mode separation itself and the framing shifts accordingly.**
- **Why Turtle Soup.** The game gives the agent a paradoxical scenario (the 汤面 "surface") and hides the story (the 汤底 "base"); the agent asks yes/no questions to reconstruct it. Three properties make it an ideal behavioral microscope: (i) the questioning protocol is a naturally verbalized search trace — no probing or activation access needed, the behavior *is* text; (ii) puzzles are deliberately under-determined, so the *direction* of each associative jump is diagnostic; (iii) games are short, language-only, and cheap to run at scale.
- **The gap** (condensed from our positioning table, §2): prior turtle-soup benchmarks (TurtleBench, SPLAT, TurtleSoup-Bench) score verification correctness, solve efficiency, or consistency with the single intended story. None interprets the search behavior itself.
- **Central hypothesis (H).** An agent's per-round questions, embedded in a semantic space jointly with human word-association norms, form a *trajectory* whose geometry predicts and explains success:
  - **H1 (stalling):** failure trajectories with step size → 0 (successive questions semantically near-identical) identify agents that cannot leave a hypothesis basin; lexical novelty heuristics detect only the verbatim extreme of this mode.
  - **H2 (drifting):** failure trajectories with normal step size but increasing distance from the human association manifold identify agents that explore, but in directions no human path takes; this mode is *invisible* to lexical novelty (synonym-shuffled re-asks look "new").
  - **H3 (predictivity):** trajectory features (step-size profile, human-path distance, their interaction) predict final solve quality beyond outcome-adjacent covariates (rounds used, question count, model size), and the two failure modes have distinct signatures.
- **Contributions.** (1) The flatness result — whether interaction length buys accuracy at any scale ⚠️ *pending re-run*; (2) a behavioral-interpretation framework (trajectory geometry) that separates stalling from unbanked exploration, with an honest account of what it does and does not predict; (3) an open-source dual-agent harness, a **22-puzzle set restricted to puzzles humans have played and solved**, and a composite score decoupling clue recall from judged causal logic; (4) a puzzle-level difficulty measure (**under-determination**) that is independent of rounds used, so it can group an accuracy-versus-rounds analysis without the grouping variable and the axis being the same quantity.

> ⚠️ **引言的钩子待重写。**现版以 flatness 开篇，但那个结果来自已作废的题集。
> 重跑后确认结论方向再定：若仍平坦，保持现有开篇；若不平坦，
> 主线要改为「轨迹几何区分失败模式」而非「更多交互无用」。

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

### 3.2 Puzzles

A puzzle nobody has solved carries no evidence that its clues suffice, that its solution is unique, or that the intended leap is reachable — an agent scoring zero on one teaches us nothing. Our set therefore takes only puzzles with a public record of human play: 22 items from a Chinese Turtle Soup community site, each keeping its source URL. Surfaces run 9–108 characters (median 34), solutions 13–200 (median 102), with 97 annotated key clues. Provenance is enforced in code — a verified family and a quarantined generated family, with tests that fail if the two mix — because the grid in §5 ran on an earlier set in which only two of eleven puzzles were real.

Each puzzle carries an **under-determination** score: how far the surface alone leaves you from the solution, measured by sampling twelve cold guesses from the surface with no Oracle feedback and taking the closest. It ranges 0.173–0.577 (median 0.347) over the set and is *not* explained by surface length (r = −0.22, n.s.), so it is available as a puzzle-level covariate — the thing §5.3's mixed-effects model currently lacks.

### 3.3 Outcome scoring: composite, not surface

Judged outcome = **clue recall (70)** + **causal-logic identity (30)**:
- Clue recall: matching against per-puzzle annotated key clues — objective, reproducible, difficulty-banded by clue count.
- Causal logic: an LLM judge rates only whether the causal chain (cause → mechanism → outcome) matches, explicitly instructed to ignore wording; sampled k=3 and averaged, since single ratings are unstable on borderline answers.

Motivation (observed, §5): a frontier model reconstructed the hidden story's full causal chain yet scored **0.00** under clue-string matching, while the composite score correctly separated its logic (30/30) from its terminology (28/70). Conversely the gate stops "far = creative" gaming: distance without validity scores zero, per the novelty × appropriateness consensus [5, 6, 9, 10].

### 3.4 Association-trajectory instrumentation

Per round *t*: extract question keywords → embed → aggregate to a round vector \(q_t\). Two per-trace signals:
- **Step size** \(s_t = d(q_t, q_{t-1})\): the agent's associative stride (forward-flow analogue [9]).
- **Human-path distance** \(h_t = d(q_t, \mathcal{H})\): distance to the puzzle's human association set \(\mathcal{H}\), built from SWOW norms [11] seeded with the 汤面's content words (plus, optionally, human player traces where available).

Failure-mode classifier (hypothesized signatures): stalling = \(\bar{s} \to 0\), \(h\) flat; drifting = \(\bar{s}\) normal, \(h_t\) increasing. Robustness: report under two encoders; the existing lexical `question_novelty` metric is retained as the ablation baseline that H2 predicts will miss synonym-drift.

## 4. Experiment Designs

**Page budget: ~1.0 page, including the E3 table.**

### E1 — Round curve (does interaction help, and when does behavior degrade?)

After every round, force a checkpoint answer and score it (clue-recall component only, keeping checkpoints cheap); plot accuracy vs. round 1…30. Full grid: the released puzzle set × 3 questioner models × 3 seeds, strong fixed Oracle. (The grid reported in §5 predates the set described in §3.2 and is scoped there.) Behavioral reading: where curves plateau, do trajectories stall (H1) or drift (H2)? Prediction: plateau onset co-occurs with step-size collapse for small models, with drift for mid-size reasoning models.

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

## 5. Results

> ⚠️ **本节整体待填 —— 实验尚未重跑。**
>
> 旧的 693 局跑在**已作废的题集**上（11 道里 6 道 LLM 生成、2 道手工添加），
> 与发布的 22 道零重叠，且当时 Oracle 与 Questioner 同家族、锚点含汤底信息、
> token 预算过低导致部分轮次为空。**那批数字已全部从本稿删除**，
> 不作为 preliminary 保留 —— 它们无法与新结果并置，留着只会误导。

### 需要产生的数据

| 小节 | 需要什么 | 依赖 |
|------|---------|------|
| 5.1 E1 轮数曲线 | 逐轮 checkpoint 准确率，各模型 | 重跑 E1 |
| 5.1 提交行为 | 各模型主动提交的比例与平均轮次 | 同上 |
| 5.2 E2 预算 | 各 cap 下的终局准确率 | 重跑 E2 |
| 5.3 E3 几何 | 逐轮步长、逐轮锚点距离（**两个锚点都要**） | 重跑 + 记录逐轮量 |
| 5.3 H3 | 混合效应模型，题目为随机截距，**欠定度作为题目层协变量** | 上述数据齐备后 |

### 重跑前必须确认（否则跑完仍缺数据）

- Oracle 与逻辑裁判**与 Questioner 不同家族**，且审计准确率 ≥90%
- **保存逐轮步长与逐轮距离** —— 目前只存汇总量，核心图因此画不出来
- **两个锚点都算**（`surface_only` / `with_solution`）
- 跑前做可跑性预检，确认 token 预算对全部 22 道足够
- `qa_rounds` 入库，否则 E3 无法复核

## 6. Harness Observations

> 以下四条**不依赖已作废的网格**，来自当前工具链，可保留。
> 每条都是这类 benchmark 的陷阱，而非本文的主张 —— 控制在半页内。

1. **原地打转是真实存在的，而词面指标只看得到一半。**小模型在后期会逐字重复更早的提问；
   词面新颖度能抓到这种极端情形，抓不到用新措辞重问同一假设的情形。
2. **表层评分会误判。**内容相同的两个答案可能因用词不同而得分相差数倍；
   把线索约束到足够长之后，两者得分一致。**这也意味着复合评分中逻辑分的必要性需要重新论证** ——
   它当初要补的洞，很大一块是线索质量造成的。
3. **被截断的思考会伪装成行为。**token 预算不足时，模型输出的"提问"是被截断的思维链片段，
   Oracle 对着没有问句的字符串作答。从记录上看，这与"Agent 不会提问"无法区分。
   解码配置是环境的一部分。
4. **线性可解的题不是好探针。**强模型能直线解出的题无法区分 Agent，
   这正是需要按欠定度给题目分级的理由。

## 7. Limitations & Ethics

**Page budget: ~0.2 page.** Keyword extraction and encoders are themselves models (audited, dual-encoder reporting); SWOW norms are population averages, not a normative standard for "correct" association — distance from them is a *descriptive* behavioral coordinate, and we explicitly do not equate human-unlike with wrong (H2 is about failure *correlation*, tested, not assumed); judge biases mitigated per [7, 8]; puzzles involve death/dark themes — content-flagged; contamination handled by memorization probes and fresh/novel puzzle sourcing.

## 8. Conclusion

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

## Appendix A — The validation set

**Where the puzzles come from.** Only items with a public record of human play are used: the 经典-tagged set of a Chinese Turtle Soup community site, each retaining its source URL. Two rounds of human review removed puzzles that were deduction rather than lateral, that had solutions long enough to need very large token budgets, or whose surfaces the site itself had truncated. A further three were dropped because our difficulty annotation failed on them — a limit of the annotation method, not a defect in the puzzles.

**One game, in full.** ⚠️ *Table to be regenerated from the re-run.* Four columns per round: the Questioner's question, the Oracle's 是/不是/与此无关, **the full story the Questioner is forced to commit that round, and that story's score**. The third and fourth columns are the point — E1 forces a checkpoint every round, and each point on the accuracy curve is one of them; a table of questions alone leaves the reader unable to see where the curve comes from. A pilot on `refsoup_008` showed the shape worth looking for: the first-round answer already named the balloon, the jettisoned luggage and the fall, and confirming the lottery four rounds later did not improve on it. If that holds in the re-run, the flatness of §5 is visible inside a single game — but the pilot's scores predate the current clue set and are not carried over.

**How difficulty is judged.** Under-determination, as in §3.2. Closeness is embedding similarity to the solution rather than clue recall, because a cold guess that reaches the right mechanism in its own words would otherwise score zero and the index would measure vocabulary. We first tried to separate *depth* (the solution sits far from the surface) from *breadth* (many stories fit it); measured separately both saturated, and they are not independent — a surface loose enough to admit many mechanisms is, for that reason, one whose true mechanism takes more reframing to reach. Over the set, under-determination is uncorrelated with surface length and correlates weakly with clue count (ρ = −0.46, p = 0.03, one of four tests at n = 22).

**How accuracy is measured.** Clue recall (70) plus causal-logic identity (30), the latter judged by a model told to ignore wording and sampled three times. Clue matching falls back to character-bigram recall when the literal string is absent, which imposes a floor on clue length: a clue too short for that fallback can only match verbatim, so two answers with the same content can score several times apart purely because one happened to use the annotated word. Requiring longer clues removes that gap. **This weakens the original case for the logic half** — much of what it compensated for was clue quality rather than a limit of lexical matching — and whether thirty points are earned is an open question we would rather state than paper over. ⚠️ *Settling it needs the re-run: compare clue-only and composite rankings across the set.*

**A caveat we report either way.** The two lowest-scoring puzzles are the two most widely circulated ones. Their surfaces may be easy to complete not because the inference is short but because the story is in the training data, in which case the measure reads familiarity as much as difficulty. A memorisation probe — asking for the solution with no surface given — separates the two and belongs in any use of this measure.

---

## Open questions for the authors (feedback wanted before v0.4)

*(Resolved: v0.1 decisions 2 & 5 — grid ran, Figure 1 real. v0.2 decisions 1 & 5 — abstract/intro now lead with flatness; mixed-effects ran: H3 not supported within-puzzle, so the paper claims geometry as interpretive, not predictive.)*

1. **H3 framing after the re-run.** The earlier grid found puzzle identity absorbing the drift signal, which is why the claim is "interpretive instrument" rather than "predictor." The re-run now has a puzzle-level covariate the old one lacked — under-determination — so the same test can ask whether difficulty is what the puzzle random effect was standing in for. Keep the softened framing regardless of how it comes out?
2. **H1 framing:** stride's sign inverting with scale is written as "H1 refined." Restate H1 in the intro instead, so the refinement isn't framed as a miss?
3. **Human data (still open):** the manifold remains the documented proxy. SWOW-zh sourcing or a small human-trace collection would strengthen H2's between-puzzle claim. Feasible before the deadline?
4. **Title (still open):** "Thinking Sideways, Observed" — alternatives welcome.
5. **Length check:** with results in, content now runs ~4.3 pages before references in the current layout; next trim pass would tighten §2 and §6. OK to trim there?
