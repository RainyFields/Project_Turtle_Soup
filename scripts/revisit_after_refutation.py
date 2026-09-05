#!/usr/bin/env python3
"""Can the feedback finding be explained away as rational information use?

是 is the rare answer (18-26% of yes/no replies), so it carries four to eight
times the surprisal of a 不是. A searcher allocating step size by information
content should therefore move further after a confirmation - which is what we
observe, and which would make the behaviour correct rather than inverted.

Separating the two needs a signal that does not depend on step size. This one
does not: whether the next question lands nearer to questions the agent has
already asked (excluding the one it just asked) than to that immediately
preceding question. A rational narrow test takes a small step somewhere new; a
return to covered ground is not that.

    python scripts/revisit_after_refutation.py
"""
import json, glob, statistics as st, random, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from evaluation.trajectory import extract_keywords, embed
random.seed(0)
MAP={"Qwen/Qwen3.5-4B":"4B","Qwen/Qwen3.6-27B":"27B","Qwen/Qwen3.5-397B-A17B":"397B"}
BINS=[(1,5),(6,10),(11,15),(16,20),(21,25),(26,30)]
rows=[]
for f in sorted(glob.glob(str(Path(__file__).resolve().parents[1] / "results/grid_2026_09/*/curve/round_curve.json"))):
    d=json.load(open(f)); m=MAP[d["questioner"]["model"]]
    for g in d["results"]:
        qa=g.get("qa_rounds") or []
        kw=[extract_keywords(r["question"]) for r in qa]
        keep=[(k,r) for k,r in zip(kw,qa) if k]
        if len(keep)<4: continue
        flat=[w for k,_ in keep for w in k]
        V=embed(flat)
        Q=[]; i=0
        for k,_ in keep:
            v=V[i:i+len(k)].mean(axis=0); Q.append(v/(np.linalg.norm(v)+1e-9)); i+=len(k)
        Q=np.stack(Q); ans=[r["answer"].strip() for _,r in keep]
        for t in range(1,len(Q)-1):          # 需要 j<t 的历史
            a=ans[t]
            kind="yes" if a.startswith("是") else "no" if a.startswith("不是") else None
            if kind is None: continue
            stride=float(1-Q[t+1]@Q[t])
            hist=float(min(1-Q[t+1]@Q[j] for j in range(t)))   # 不含紧邻的第 t 个
            b=next((i for i,(lo,hi) in enumerate(BINS) if lo<=t+1<=hi), len(BINS)-1)
            back = 1.0 if hist < stride else 0.0   # 离更早的问题比离刚问的还近 = 回头
            rows.append((m, g["puzzle_id"], b, kind, stride, hist, back))
print(f"配对样本 {len(rows)}", flush=True)
def boot(byp,n=3000):
    ks=list(byp); v=[x for k in ks for x in byp[k]]
    b=sorted(st.mean([x for k in (random.choice(ks) for _ in ks) for x in byp[k]]) for _ in range(n))
    return st.mean(v), b[int(.025*n)], b[int(.975*n)-1], len(v)
print("\n=== 「不是」之后的下一问，与之前问过的问题的最小距离 ===")
print("   （越小 = 越是回到已经问过的地方）\n")
print(f"{'':6s}{'stride 差(是−不是)':>22s}{'与历史最小距离 差(是−不是)':>30s}")
for m in ["4B","27B","397B"]:
    cell=defaultdict(lambda: {"yes":[], "no":[]})
    for mm,p,b,k,s,h,bk in rows:
        if mm==m: cell[(p,b)][k].append((s,h,bk))
    bs=defaultdict(list); bh=defaultdict(list); bb=defaultdict(list)
    ry=[]; rn=[]
    for (p,b),v in cell.items():
        if v["yes"] and v["no"]:
            bs[p].append(st.mean(x[0] for x in v["yes"])-st.mean(x[0] for x in v["no"]))
            bh[p].append(st.mean(x[1] for x in v["yes"])-st.mean(x[1] for x in v["no"]))
            bb[p].append(st.mean(x[2] for x in v["no"])-st.mean(x[2] for x in v["yes"]))
    for mm,p,b,k,s_,h_,bk in rows:
        if mm==m: (ry if k=="yes" else rn).append(bk)
    a1,l1,h1,n1=boot(bs); a2,l2,h2,n2=boot(bh); a3,l3,h3,n3=boot(bb)
    s1="✅" if l1>0 else "—"; s2="✅" if l2>0 else "—"; s3="✅" if l3>0 else ("—" if l3<=0<=h3 else "↓")
    print(f"  {m:5s}{a1:>+11.4f} [{l1:+.4f},{h1:+.4f}]{s1}{a2:>+15.4f} [{l2:+.4f},{h2:+.4f}]{s2}")
    print(f"        回头率  「不是」后 {st.mean(rn):.1%}  vs 「是」后 {st.mean(ry):.1%}   差 {a3:+.3f} [{l3:+.3f},{h3:+.3f}]{s3}")
