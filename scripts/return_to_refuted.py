#!/usr/bin/env python3
"""After a refutation, does the next question move toward what was already ruled out?

This replaces an earlier argument that rested on step size, and it does so
because that argument needed a premise neither we nor an objector could
establish: whether a refutation ought to produce a larger jump than a
confirmation. Surprisal, belief change, and distance in question space are three
different quantities, and nothing licenses reading one off another.

This test needs no such premise. For each round we ask whether the next question
lands nearer to regions the Oracle has already refuted or to regions it has
already confirmed. Moving toward refuted ground is wasteful under any account of
search. The obvious objection - that refutations outnumber confirmations three
to one, so a minimum over the larger set is smaller by construction - is
answered by the control: the same imbalance holds after a confirmation, where no
asymmetry appears.

    python scripts/return_to_refuted.py
"""
import json, glob, statistics as st, random, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from evaluation.trajectory import extract_keywords, embed
random.seed(0)
MAP={"Qwen/Qwen3.5-4B":"4B","Qwen/Qwen3.6-27B":"27B","Qwen/Qwen3.5-397B-A17B":"397B"}
rows=[]
for f in sorted(glob.glob(str(Path(__file__).resolve().parents[1] / "results/grid_2026_09/*/curve/round_curve.json"))):
    d=json.load(open(f)); m=MAP[d["questioner"]["model"]]
    for g in d["results"]:
        qa=g.get("qa_rounds") or []
        kw=[extract_keywords(r["question"]) for r in qa]
        keep=[(k,r) for k,r in zip(kw,qa) if k]
        if len(keep)<6: continue
        flat=[w for k,_ in keep for w in k]; V=embed(flat)
        Q=[]; i=0
        for k,_ in keep:
            v=V[i:i+len(k)].mean(axis=0); Q.append(v/(np.linalg.norm(v)+1e-9)); i+=len(k)
        Q=np.stack(Q)
        kind=[]
        for _,r in keep:
            a=r["answer"].strip()
            kind.append("yes" if a.startswith("是") else "no" if a.startswith("不是") else "irr")
        for t in range(2,len(Q)-1):
            if kind[t]=="irr": continue
            # 已问过且得到「不是」的位置 / 得到「是」的位置（都在 t 之前，不含 t）
            refuted=[j for j in range(t) if kind[j]=="no"]
            confirmed=[j for j in range(t) if kind[j]=="yes"]
            if not refuted or not confirmed: continue
            dR=min(1-Q[t+1]@Q[j] for j in refuted)
            dC=min(1-Q[t+1]@Q[j] for j in confirmed)
            rows.append((m,g["puzzle_id"],kind[t],dR,dC))
print(f"样本 {len(rows)}",flush=True)
print("\n=== 下一问离「曾被否定的区域」有多近，vs 离「曾被确认的区域」 ===")
print("   （越小=越近。回到被否定过的地方 = 浪费；回到被确认过的地方 = 合理深挖）\n")
def bs(byp,n=3000):
    ks=list(byp); v=[x for k in ks for x in byp[k]]
    b=sorted(st.mean([x for k in (random.choice(ks) for _ in ks) for x in byp[k]]) for _ in range(n))
    return st.mean(v), b[int(.025*n)], b[int(.975*n)-1], len(v)
print(f"{'':6s}{'收到不是之后':>34s}{'收到是之后':>34s}")
print(f"{'':6s}{'d(被否定) − d(被确认)':>34s}{'d(被否定) − d(被确认)':>34s}")
for m in ["4B","27B","397B"]:
    out=""
    for k in ("no","yes"):
        byp=defaultdict(list)
        for mm,p,kk,dR,dC in rows:
            if mm==m and kk==k: byp[p].append(dR-dC)
        if not byp: out+=f"{'n/a':>34s}"; continue
        a,l,h,n=bs(byp)
        mark="✅" if h<0 else ("↑" if l>0 else " ")
        out+=f"{a:>+18.4f} [{l:+.3f},{h:+.3f}]{mark}"
    print(f"  {m:5s}{out}")
print("\n  负值 = 下一问离「被否定过的」比离「被确认过的」更近")
