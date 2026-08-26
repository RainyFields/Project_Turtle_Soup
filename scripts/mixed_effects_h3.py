#!/usr/bin/env python3
"""H3: do trajectory features predict outcome beyond covariates?

Mixed-effects models over the 99 E1 traces (docs/paper/figures/e3_geometry.json):
puzzle as random intercept, model tier as fixed effect (only 3 levels — too few
for a random effect), ML fits compared by likelihood-ratio test and AIC.

  M0 (covariates):      best_acc ~ tier
  M1 (+drift):          best_acc ~ tier + z_hslope
  M2 (+stride x tier):  best_acc ~ tier + z_hslope + z_step : tier

Writes docs/paper/figures/h3_mixed_effects.json and prints a summary.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats


def lrt(m_small, m_big):
    stat = 2 * (m_big.llf - m_small.llf)
    df = m_big.df_modelwc - m_small.df_modelwc
    p = float(stats.chi2.sf(stat, df))
    return {"chi2": round(float(stat), 3), "df": int(df), "p": round(p, 5)}


def main() -> int:
    src = ROOT / "docs/paper/figures/e3_geometry.json"
    rows = json.loads(src.read_text())["traces"]
    df = pd.DataFrame(rows)
    df = df.rename(columns={"label": "tier"})
    for col in ("mean_step", "human_dist_slope"):
        df["z_" + col.split("_")[-1] if col == "mean_step" else "z_hslope"] = 0  # placeholder
    df["z_step"] = (df["mean_step"] - df["mean_step"].mean()) / df["mean_step"].std()
    df["z_hslope"] = (df["human_dist_slope"] - df["human_dist_slope"].mean()) / df[
        "human_dist_slope"
    ].std()
    print(f"n={len(df)} traces, {df['puzzle_id'].nunique()} puzzles, tiers: {sorted(df['tier'].unique())}")

    kw = dict(groups=df["puzzle_id"], data=df)
    m0 = smf.mixedlm("best_acc ~ C(tier)", **kw).fit(reml=False)
    m1 = smf.mixedlm("best_acc ~ C(tier) + z_hslope", **kw).fit(reml=False)
    m2 = smf.mixedlm("best_acc ~ C(tier) + z_hslope + z_step:C(tier)", **kw).fit(reml=False)

    out = {
        "n": len(df),
        "models": {
            "M0_covariates": {"aic": round(m0.aic, 1), "llf": round(m0.llf, 2)},
            "M1_plus_drift": {"aic": round(m1.aic, 1), "llf": round(m1.llf, 2)},
            "M2_plus_stride_x_tier": {"aic": round(m2.aic, 1), "llf": round(m2.llf, 2)},
        },
        "lrt_M0_vs_M1_drift": lrt(m0, m1),
        "lrt_M1_vs_M2_stride_x_tier": lrt(m1, m2),
        "m2_fixed_effects": {
            k: {"coef": round(float(v), 4), "p": round(float(m2.pvalues[k]), 5)}
            for k, v in m2.params.items()
            if k != "Group Var"
        },
        "random_intercept_var_puzzle": round(float(m2.cov_re.iloc[0, 0]), 5),
    }
    dst = ROOT / "docs/paper/figures/h3_mixed_effects.json"
    dst.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nWrote {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
