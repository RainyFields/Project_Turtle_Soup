#!/usr/bin/env python3
"""Analyses answering the 2026-09-04 simulated review's major concerns.

S1  Retention estimator, bootstrap CIs, and a within-game permutation (jitter)
    null: does observed final-vs-sustained-peak retention sit below what a
    knowledge-constant but jitter-noisy series would produce?
S2  Question well-formedness by model (truncation-artifact audit) and 4B E2
    accuracy conditioned on non-exhausted games, exhaustion by cap.
S7  Stride main-effect LRT and coefficient CIs for the mixed model; the same
    drift test under the surface-only anchor.
R3-M6  E1 checkpoint mean at round k versus E2 cap-k final, per model.
S10 Per-game correlation between score halves and logic-judge inter-sample
    agreement.

Writes docs/paper/figures/review_response.json.
  .venv/bin/python scripts/review_response_analyses.py
"""
from __future__ import annotations

import glob
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RNG = random.Random(0)
NP_RNG = np.random.default_rng(0)


def model_of(path: str) -> str:
    return (
        Path(path).parts[-3].rsplit("_s", 1)[0]
        .replace("Qwen_Qwen", "Qwen")
        .replace("-A17B", "")
    )


def load_e1():
    games = defaultdict(list)
    for f in sorted(glob.glob(str(ROOT / "results/grid_2026_09/*/curve/round_curve.json"))):
        m = model_of(f)
        for r in json.load(open(f))["results"]:
            acc = {int(k): v for k, v in (r.get("accuracy_by_round") or {}).items()}
            if len(acc) < 2:
                continue
            vals = [acc[rd] for rd in sorted(acc)]
            games[m].append(
                dict(
                    vals=vals,
                    committed=r.get("natural_end_round") is not None,
                    qa=[row.get("question", "") for row in (r.get("qa_rounds") or [])],
                )
            )
    return games


def sustained_peak(vals):
    return max(min(vals[i], vals[i + 1]) for i in range(len(vals) - 1))


def retention_stats(games):
    """S1: estimators, bootstrap CIs, permutation null."""
    out = {}
    for m, gs in games.items():
        peaks = np.array([sustained_peak(g["vals"]) for g in gs])
        finals = np.array([g["vals"][-1] for g in gs])
        keep = peaks > 0
        # Estimator A (reported): mean of per-game final/sustained-peak ratios,
        # over games with a nonzero sustained peak.
        ratios = finals[keep] / peaks[keep]
        # Estimator B: ratio of means (all games).
        rom = finals.mean() / peaks.mean()
        # Bootstrap CI over games for estimator A.
        boots = []
        idx = np.arange(keep.sum())
        for _ in range(4000):
            s = NP_RNG.choice(idx, size=len(idx), replace=True)
            boots.append(ratios[s].mean())
        lo, hi = np.percentile(boots, [2.5, 97.5])
        # Permutation null: within each game, shuffle the checkpoint order
        # (knowledge-constant, jitter-only null); recompute retention.
        null_means = []
        for _ in range(2000):
            r_ratios = []
            for g in gs:
                v = list(g["vals"])
                RNG.shuffle(v)
                p = sustained_peak(v)
                if p > 0:
                    r_ratios.append(v[-1] / p)
            null_means.append(float(np.mean(r_ratios)))
        null_means = np.array(null_means)
        p_below = float((null_means <= ratios.mean()).mean())
        # Retention excluding early-committing games.
        nc = [g for g in gs if not g["committed"]]
        nc_peaks = np.array([sustained_peak(g["vals"]) for g in nc])
        nc_finals = np.array([g["vals"][-1] for g in nc])
        k2 = nc_peaks > 0
        out[m] = dict(
            n=len(gs),
            n_nonzero_peak=int(keep.sum()),
            retention_mean_of_ratios=round(float(ratios.mean()), 3),
            retention_ci95=[round(float(lo), 3), round(float(hi), 3)],
            retention_ratio_of_means=round(float(rom), 3),
            null_mean_retention=round(float(null_means.mean()), 3),
            null_ci95=[round(float(np.percentile(null_means, 2.5)), 3),
                       round(float(np.percentile(null_means, 97.5)), 3)],
            p_observed_at_or_below_null=round(p_below, 4),
            retention_excl_committed=round(float((nc_finals[k2] / nc_peaks[k2]).mean()), 3),
        )
    return out


QUESTION_MARKS = ("？", "?")
QUESTION_WORDS = re.compile(r"吗|是否|是不是|有没有|与.*有关|是因为")


def wellformed_stats(games):
    """S2: fraction of logged questions that look like well-formed questions."""
    out = {}
    for m, gs in games.items():
        total = ok = 0
        for g in gs:
            for q in g["qa"]:
                total += 1
                qs = q.strip()
                if qs.endswith(QUESTION_MARKS) or QUESTION_WORDS.search(qs[-25:]):
                    ok += 1
        out[m] = dict(rounds=total, wellformed=ok,
                      frac=round(ok / total, 4) if total else None)
    return out


def e2_conditional():
    """S2/R1-M4: 4B exhaustion by cap; accuracy conditional on non-exhausted."""
    rows = defaultdict(lambda: defaultdict(list))
    for f in sorted(glob.glob(str(ROOT / "results/grid_2026_09/*/caps/round_cap_sweep.json"))):
        m = model_of(f)
        for r in json.load(open(f))["results"]:
            cap = r.get("cap") or r.get("round_cap")
            rows[m][cap].append((r["score"], r["terminated_by"]))
    out = {}
    for m, caps in rows.items():
        out[m] = {}
        for cap, lst in sorted(caps.items()):
            exh = [s for s, t in lst if t == "token_budget"]
            non = [s for s, t in lst if t != "token_budget"]
            out[m][str(cap)] = dict(
                n=len(lst),
                exhausted=len(exh),
                mean_all=round(float(np.mean([s for s, _ in lst])), 3),
                mean_nonexhausted=round(float(np.mean(non)), 3) if non else None,
            )
    return out


def e1_vs_e2(games):
    """R3-M6: E1 checkpoint mean at round k vs E2 cap-k final mean."""
    e2 = e2_conditional()
    out = {}
    for m, gs in games.items():
        out[m] = {}
        for k in (5, 10, 15, 20, 25, 30):
            vals = [g["vals"][k - 1] for g in gs if len(g["vals"]) >= k]
            e2k = e2[m].get(str(k), {})
            out[m][str(k)] = dict(
                e1_checkpoint_mean=round(float(np.mean(vals)), 3),
                e2_cap_final_mean=e2k.get("mean_all"),
                e2_cap_final_nonexhausted=e2k.get("mean_nonexhausted"),
            )
    return out


def mixed_model_extras():
    """S7: stride main effect, coefficient CIs, surface-anchor stride test."""
    import pandas as pd
    import statsmodels.formula.api as smf
    from scipy import stats as st

    d = json.load(open(ROOT / "docs/paper/figures/e3_geometry.json"))["traces"]
    df = pd.DataFrame(d).rename(columns={"label": "tier"})
    for col, z in (("mean_step", "z_step"), ("human_dist_slope", "z_hslope"),
                   ("surface_human_dist_slope", "z_surf")):
        df[z] = (df[col] - df[col].mean()) / df[col].std()
    kw = dict(groups=df["puzzle_id"], data=df)
    m0 = smf.mixedlm("best_acc ~ C(tier)", **kw).fit(reml=False)

    def lrt(big):
        s = 2 * (big.llf - m0.llf)
        return round(float(st.chi2.sf(s, big.df_modelwc - m0.df_modelwc)), 4)

    out = {}
    for name, term in (("stride_main", "z_step"), ("drift_main", "z_hslope"),
                       ("surface_drift_main", "z_surf")):
        m1 = smf.mixedlm(f"best_acc ~ C(tier) + {term}", **kw).fit(reml=False)
        ci = m1.conf_int().loc[term]
        out[name] = dict(
            coef=round(float(m1.params[term]), 4),
            ci95=[round(float(ci[0]), 4), round(float(ci[1]), 4)],
            lrt_p=lrt(m1),
        )
    out["spec"] = ("response = best checkpoint accuracy per game; Gaussian LMM, "
                   "puzzle random intercept, tier fixed effect, ML fits, LRTs")
    return out


def subscore_stats():
    """S10: per-game correlation between halves; judge inter-sample agreement."""
    from scipy import stats as st
    per = defaultdict(lambda: ([], []))
    agree = []
    for f in sorted(glob.glob(str(ROOT / "results/grid_2026_09/*/caps/round_cap_sweep.json"))):
        m = model_of(f)
        for r in json.load(open(f))["results"]:
            det = r.get("score_detail") or {}
            if "key_clue_score" in det:
                per[m][0].append(det["key_clue_score"])
                per[m][1].append(det.get("logic_score", 0))
            samples = det.get("logic_samples") or []
            if len(samples) == 2:
                agree.append(abs(samples[0] - samples[1]))
    out = {}
    for m, (kc, lg) in per.items():
        rho = st.spearmanr(kc, lg)
        out[m] = dict(n=len(kc), spearman=round(float(rho.statistic), 3),
                      p=round(float(rho.pvalue), 5))
    out["judge_intersample_mean_absdiff_of30"] = (
        round(float(np.mean(agree)), 2) if agree else None)
    out["judge_intersample_exact_agreement"] = (
        round(float(np.mean([a == 0 for a in agree])), 3) if agree else None)
    return out


if __name__ == "__main__":
    games = load_e1()
    result = dict(
        retention=retention_stats(games),
        wellformed=wellformed_stats(games),
        e2_conditional=e2_conditional(),
        e1_vs_e2=e1_vs_e2(games),
        mixed_model=mixed_model_extras(),
        subscores=subscore_stats(),
    )
    dst = ROOT / "docs/paper/figures/review_response.json"
    dst.write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))
