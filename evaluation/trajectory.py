"""Association-trajectory instrumentation (E3) and Figure 1 rendering.

Per game: embed each round's question keywords into a semantic space and
compute two signals —
  step size   s_t = d(q_t, q_{t-1})   (associative stride; forward-flow analogue)
  human dist  h_t = d(q_t, H)         (distance to the puzzle's association anchor)

H is currently a *proxy manifold*: content words of the puzzle surface,
solution, and key clues. The paper's full design anchors H in SWOW human
word-association norms; the proxy is documented as such wherever plotted.

Heavy deps (jieba, sentence-transformers) import lazily so the test suite and
game harness never pay for them.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

_STOP = set(
    "的 了 是 吗 呢 他 她 它 我 你 这 那 有 没有 不 在 与 和 或 因为 所以 但是 如果 就 都 也 很 请 什么 为什么 怎么 是否 一个 一些 还是 而且 自己 他们 她们 我们 是不是 有没有 关于 其中 这个 那个 时候 事情 东西 地方 可能 应该 需要 进行 存在 发生 导致 出现 使用 通过 已经 曾经 正在 最终 最后 开始 之前 之后 目前 现在".split()
)


def extract_keywords(text: str) -> List[str]:
    """Content words of one question/answer. Same extractor for every model."""
    import jieba

    words = jieba.lcut(re.sub(r"[A-Za-z0-9_\s]+", " ", text))
    out, seen = [], set()
    for w in words:
        w = w.strip()
        if len(w) >= 2 and w not in _STOP and re.search(r"[一-鿿]", w) and w not in seen:
            seen.add(w)
            out.append(w)
    return out


_MODEL_CACHE: Dict[str, Any] = {}


def _encoder(name: str = "BAAI/bge-small-zh-v1.5"):
    if name not in _MODEL_CACHE:
        from sentence_transformers import SentenceTransformer

        _MODEL_CACHE[name] = SentenceTransformer(name)
    return _MODEL_CACHE[name]


def embed(texts: List[str], encoder_name: str = "BAAI/bge-small-zh-v1.5"):
    import numpy as np

    if not texts:
        return np.zeros((0, 512))
    vecs = _encoder(encoder_name).encode(texts, normalize_embeddings=True)
    return np.asarray(vecs)


@dataclass
class TraceGeometry:
    label: str
    puzzle_id: str
    round_vectors: Any  # (T, d) unit vectors
    round_keywords: List[List[str]]
    step_sizes: List[float]  # cosine distance q_t vs q_{t-1}
    human_dists: List[float]  # cosine distance q_t vs proxy manifold
    extra: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        import numpy as np

        s, h = self.step_sizes, self.human_dists
        return {
            "label": self.label,
            "puzzle_id": self.puzzle_id,
            "rounds": len(self.round_keywords),
            "mean_step": round(float(np.mean(s)), 4) if s else None,
            "late_step": round(float(np.mean(s[len(s) // 2 :])), 4) if s else None,
            "mean_human_dist": round(float(np.mean(h)), 4) if h else None,
            "human_dist_slope": (
                round(float(np.polyfit(range(len(h)), h, 1)[0]), 5) if len(h) >= 3 else None
            ),
            **self.extra,
        }


def proxy_manifold_terms(puzzle: Dict[str, Any]) -> List[str]:
    """Proxy for the human association manifold H (pending SWOW norms)."""
    text = " ".join(
        [puzzle.get("surface", ""), puzzle.get("solution", "")] + list(puzzle.get("key_clues", []))
    )
    return extract_keywords(text)


def trace_geometry(
    qa_rounds: List[Dict[str, Any]],
    puzzle: Dict[str, Any],
    *,
    label: str,
    encoder_name: str = "BAAI/bge-small-zh-v1.5",
) -> Optional[TraceGeometry]:
    import numpy as np

    per_round_kw = [extract_keywords(r["question"]) for r in qa_rounds]
    keep = [(kw, r) for kw, r in zip(per_round_kw, qa_rounds) if kw]
    if len(keep) < 2:
        return None
    per_round_kw = [kw for kw, _ in keep]

    # Round vector = mean of keyword embeddings, re-normalized.
    flat = [w for kws in per_round_kw for w in kws]
    vecs = embed(flat, encoder_name)
    round_vecs, i = [], 0
    for kws in per_round_kw:
        v = vecs[i : i + len(kws)].mean(axis=0)
        round_vecs.append(v / (np.linalg.norm(v) + 1e-9))
        i += len(kws)
    Q = np.stack(round_vecs)

    steps = [float(1 - Q[t] @ Q[t - 1]) for t in range(1, len(Q))]

    manifold_terms = proxy_manifold_terms(puzzle)
    M = embed(manifold_terms, encoder_name)
    # distance to manifold = 1 - mean of top-3 keyword-level similarities
    hdists = []
    for t in range(len(Q)):
        sims = np.sort(M @ Q[t])[::-1][:3]
        hdists.append(float(1 - sims.mean()))

    return TraceGeometry(
        label=label,
        puzzle_id=puzzle["id"],
        round_vectors=Q,
        round_keywords=per_round_kw,
        step_sizes=steps,
        human_dists=hdists,
    )


def figure1(
    traces: List[TraceGeometry],
    puzzle: Dict[str, Any],
    out_path: Path,
    *,
    encoder_name: str = "BAAI/bge-small-zh-v1.5",
    title: str = "",
) -> Path:
    """2-D projection: proxy manifold cloud + per-model question trajectories."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    matplotlib.rcParams["font.family"] = [
        "Arial Unicode MS", "PingFang SC", "Hiragino Sans GB", "sans-serif",
    ]

    manifold_terms = proxy_manifold_terms(puzzle)
    M = embed(manifold_terms, encoder_name)
    stack = np.vstack([M] + [t.round_vectors for t in traces])
    mu = stack.mean(axis=0)
    X = stack - mu
    # PCA via SVD on the combined cloud
    _, _, VT = np.linalg.svd(X, full_matrices=False)
    P = X @ VT[:2].T

    Mp = P[: len(M)]
    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    ax.scatter(Mp[:, 0], Mp[:, 1], s=90, alpha=0.15, color="tab:gray", edgecolors="none",
               label="proxy human-association manifold")
    for term, (x, y) in list(zip(manifold_terms, Mp))[:12]:
        ax.annotate(term, (x, y), fontsize=7, alpha=0.55, ha="center")

    colors = ["tab:red", "tab:blue", "tab:green", "tab:purple"]
    off = len(M)
    for c, tr in zip(colors, traces):
        Tp = P[off : off + len(tr.round_vectors)]
        off += len(tr.round_vectors)
        ax.plot(Tp[:, 0], Tp[:, 1], marker="o", markersize=4, lw=1.4, color=c, alpha=0.85,
                label=f"{tr.label} (mean step {np.mean(tr.step_sizes):.2f})")
        ax.annotate("R1", Tp[0], fontsize=8, color=c, fontweight="bold")
        ax.annotate(f"R{len(Tp)}", Tp[-1], fontsize=8, color=c, fontweight="bold")

    ax.set_title(title or f"Question trajectories — {puzzle['id']}")
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.legend(fontsize=8, loc="best")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path


def load_qa_rows(json_path: Path) -> List[Dict[str, Any]]:
    """Rows with qa_rounds from any round-study report JSON."""
    report = json.loads(json_path.read_text())
    rows = report.get("results") or (report.get("exp1_results", []) + report.get("exp2_results", []))
    return [r for r in rows if r.get("qa_rounds")]
