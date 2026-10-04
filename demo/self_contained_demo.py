"""TrustRAG — self-contained, zero-dependency demo application.

Runs with ONLY the Python standard library (no numpy, no Qdrant, no models). It implements
the *full* retrieval pipeline on a small corpus and prints a measured report:

    dense (TF-IDF cosine) → BM25 → RRF hybrid → exact-match rerank, plus metadata
    filtering, per-mode IR metrics (Hit@5 / P@5 / R@5 / MRR / nDCG) and per-query latency.

This proves the *mechanism*; the full build (BGE embeddings + Qdrant + MS MARCO) is the
same pipeline with real components. Every number printed is computed live, nothing hard-coded.

Run:  python demo/self_contained_demo.py
"""
from __future__ import annotations

import math
import re
import time
from collections import Counter, defaultdict

TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


# --------------------------------------------------------------------------- corpus
# (id, text, category, acl_groups) — illustrative insurance-flavoured corpus.
CORPUS = [
    ("d1", "The gold health plan carries a 500 dollar deductible per year.", "plan", ["public"]),
    ("d2", "The silver health plan carries a 1000 dollar deductible per year.", "plan", ["public"]),
    ("d3", "The grace period for late premium payment is 30 days.", "billing", ["public"]),
    ("d4", "The grace period for filing a claim is 90 days.", "claims", ["public"]),
    ("d5", "Claims must be filed within 90 days of the incident.", "claims", ["public"]),
    ("d6", "Boiling an egg takes about ten minutes.", "general", ["public"]),
    ("d7", "Paris is known for the Eiffel Tower.", "general", ["public"]),
    ("d8", "The capital of France is Paris.", "general", ["public"]),
    ("d9", "Preventive care is covered at no cost under all plans.", "plan", ["public"]),
    ("d10", "Water damage from burst pipes is covered; flood damage is excluded.", "coverage", ["public"]),
    ("d11", "The out-of-pocket maximum for the gold plan is 5000 dollars.", "plan", ["public"]),
    ("d12", "Appeals must be filed within 60 days of denial.", "claims", ["public"]),
    ("d13", "The policy covers water damage caused by burst pipes only.", "coverage", ["internal"]),
]

# eval queries: {query, gold_passage_ids, reference_answer}
EVAL = [
    {"query": "what is the deductible for the gold health plan", "gold": ["d1"],
     "reference": "500 dollar deductible per year."},
    {"query": "how long does it take to boil an egg", "gold": ["d6"],
     "reference": "about ten minutes."},
    {"query": "what is the grace period for paying a late premium", "gold": ["d3"],
     "reference": "30 days."},
    {"query": "how long do I have to file a claim", "gold": ["d4", "d5"],
     "reference": "90 days."},
    {"query": "what is the capital of france", "gold": ["d8"],
     "reference": "Paris."},
    {"query": "does the policy cover flood damage", "gold": ["d10"],
     "reference": "Flood damage is excluded."},
]


# --------------------------------------------------------------------------- engine
def _df(corpus: list[str]) -> Counter:
    df = Counter()
    for doc in corpus:
        df.update(set(tokenize(doc)))
    return df


def _tfidf(doc: str, df: Counter, n: int) -> dict[str, float]:
    tf = Counter(tokenize(doc))
    out = {}
    for t, f in tf.items():
        out[t] = (1.0 + math.log(f)) * math.log(n / df[t])
    return out


def _norm(v: dict[str, float]) -> float:
    return math.sqrt(sum(x * x for x in v.values())) or 1.0


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    return sum(v * b.get(k, 0.0) for k, v in a.items()) / (_norm(a) * _norm(b))


def _bm25(query: str, doc: str, df: Counter, n: int, avgdl: float, k1: float = 1.5, b: float = 0.75) -> float:
    qtf = Counter(tokenize(query))
    dtf = Counter(tokenize(doc))
    dl = sum(dtf.values()) or 1
    score = 0.0
    for t, qf in qtf.items():
        f = dtf.get(t, 0)
        if f == 0:
            continue
        idf = math.log((n - df[t] + 0.5) / (df[t] + 0.5) + 1.0)
        score += idf * f * (k1 + 1) / (f + k1 * (1 - b + b * dl / avgdl)) * qf
    return score


def _rrf(ranked_lists: list[list[str]], k: float = 60.0) -> dict[str, float]:
    fused: dict[str, float] = defaultdict(float)
    for ranked in ranked_lists:
        for rank, pid in enumerate(ranked, start=1):
            fused[pid] += 1.0 / (k + rank)
    return fused


def _rerank(query: str, passages: list[dict]) -> list[dict]:
    """Simple exact-term-coverage reranker (stand-in for a cross-encoder)."""
    q = set(tokenize(query))
    scored = []
    for p in passages:
        coverage = len(q & set(tokenize(p["text"]))) / (len(q) or 1)
        scored.append((p["score"] + coverage, p))  # fused score + coverage bonus
    scored.sort(key=lambda x: -x[0])
    return [p for _, p in scored]


# --------------------------------------------------------------------------- metrics
def _m(gold: set[str], retrieved: list[str]):
    k5 = retrieved[:5]
    hit = 1.0 if any(r in gold for r in k5) else 0.0
    prec = sum(1 for r in k5 if r in gold) / len(k5)
    recall = sum(1 for r in k5 if r in gold) / len(gold)
    mrr = 0.0
    for i, r in enumerate(retrieved[:10], start=1):
        if r in gold:
            mrr = 1.0 / i
            break
    dcg = 0.0
    for i, r in enumerate(retrieved[:10]):
        if r in gold:
            dcg += 1.0 / math.log2(i + 2)
    ideal = sum(1.0 / math.log2(i + 2) for i in range(min(len(gold), 10)))
    ndcg = dcg / ideal if ideal else 0.0
    return hit, prec, recall, mrr, ndcg


# --------------------------------------------------------------------------- retrieval
class Retriever:
    def __init__(self, corpus: list[tuple]) -> None:
        self.docs = [d for d, *_ in corpus]
        self.meta = {pid: {"category": cat, "acl": acl} for pid, _, cat, acl in corpus}
        self.n = len(self.docs)
        self.df = _df(self.docs)
        self.avgdl = sum(len(tokenize(d)) for d in self.docs) / self.n
        self.dense = {pid: _tfidf(d, self.df, self.n) for pid, d, *_ in corpus}

    def search(self, query: str, mode: str, top_k: int = 5, category: str | None = None, groups: list[str] | None = None) -> tuple[list[str], float]:
        t0 = time.perf_counter()
        qtfidf = _tfidf(query, self.df, self.n)
        candidates = [pid for pid in self.meta if self._allowed(pid, category, groups)]

        dense_ranked = sorted(candidates, key=lambda p: -_cosine(qtfidf, self.dense[p]))
        sparse_ranked = sorted(candidates, key=lambda p: -_bm25(query, self.docs[self._idx(p)], self.df, self.n, self.avgdl))

        if mode == "dense":
            out = dense_ranked
        elif mode == "sparse":
            out = sparse_ranked
        elif mode == "hybrid":
            fused = _rrf([dense_ranked, sparse_ranked])
            out = sorted(fused, key=lambda p: -fused[p])
        elif mode == "hybrid_rerank":
            fused = _rrf([dense_ranked, sparse_ranked])
            pool = sorted(fused, key=lambda p: -fused[p])[:top_k]
            passages = [{"pid": p, "text": self.docs[self._idx(p)], "score": fused[p]} for p in pool]
            out = [p["pid"] for p in _rerank(query, passages)]
        else:
            raise ValueError(mode)
        ms = (time.perf_counter() - t0) * 1000
        return out[:top_k], round(ms, 3)

    def _idx(self, pid: str) -> int:
        return next(i for i, (d, *_c) in enumerate(CORPUS) if d == pid)

    def _allowed(self, pid: str, category: str | None, groups: list[str] | None) -> bool:
        if category is not None and self.meta[pid]["category"] != category:
            return False
        if groups is not None and not (set(self.meta[pid]["acl"]) & set(groups)):
            return False
        return True


# --------------------------------------------------------------------------- report
def main() -> None:
    r = Retriever(CORPUS)
    print("=" * 78)
    print("TrustRAG — self-contained hybrid retrieval demo (zero dependencies)")
    print("dense = TF-IDF cosine (stand-in for BGE embeddings); sparse = BM25;")
    print("hybrid = reciprocal rank fusion; hybrid_rerank = + exact-term coverage rerank.")
    print("=" * 78)

    print("\n1. The 'similar but wrong' failure (dense vs hybrid)")
    q = "what is the deductible for the gold health plan"
    for mode in ("dense", "hybrid"):
        ids, ms = r.search(q, mode)
        print(f"\n  [{mode}] {q}")
        for i, pid in enumerate(ids, 1):
            flag = "  <-- GOLD" if pid in EVAL[0]["gold"] else ""
            print(f"    #{i} {pid}: {CORPUS[r._idx(pid)][1]}{flag}")

    print("\n2. Metadata filter (category=claims)")
    ids, _ = r.search("how long do I have to file a claim", "hybrid", category="claims")
    print("   " + " | ".join(f"{pid}({r.meta[pid]['category']})" for pid in ids))

    print("\n3. Permission filter (groups=['public'] hides internal d13)")
    ids_pub, _ = r.search("water damage coverage", "hybrid", groups=["public"])
    print("   public: " + ", ".join(ids_pub))
    ids_int, _ = r.search("water damage coverage", "hybrid", groups=["internal"])
    print("   internal: " + ", ".join(ids_int))

    print("\n4. Measured IR metrics (real, computed live)")
    print(f"   {'mode':<16}{'Hit@5':>7}{'P@5':>7}{'R@5':>7}{'MRR':>7}{'nDCG':>7}{'p95-ish':>9}")
    for mode in ("dense", "sparse", "hybrid", "hybrid_rerank"):
        agg = [0.0] * 5
        lats = []
        for item in EVAL:
            ids, ms = r.search(item["query"], mode)
            lats.append(ms)
            m = _m(set(item["gold"]), ids)
            agg = [a + b for a, b in zip(agg, m)]
        n = len(EVAL)
        agg = [a / n for a in agg]
        lat = sorted(lats)[int(0.95 * (len(lats) - 1))]
        print(f"   {mode:<16}{agg[0]:>7.2f}{agg[1]:>7.2f}{agg[2]:>7.2f}{agg[3]:>7.2f}{agg[4]:>7.2f}{lat:>7.1f}ms")

    print("\n5. Live update (upsert then search)")
    CORPUS.append(("d14", "The speed limit in school zones in Texas is 20 mph.", "general", ["public"]))
    r = Retriever(CORPUS)
    ids, _ = r.search("texas school zone speed limit", "hybrid")
    print("   " + ", ".join(ids))

    print("\nEvery number above is computed live; none is hard-coded.")
    print("The full build (BGE + Qdrant + MS MARCO) runs the same pipeline at 100k scale.")


if __name__ == "__main__":
    main()
