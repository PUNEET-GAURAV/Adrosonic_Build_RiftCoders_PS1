from trustrag.core.fusion import dbsf, fuse, rrf, sort_by_fused, weighted


class Item:
    def __init__(self, pid, score):
        self.passage_id = pid
        self.score = score
        self.dense_rank = None
        self.sparse_rank = None
        self.dense_score = None
        self.sparse_score = None
        self.rerank_score = None
        self.rank = 0


def test_rrf_rewards_membership_in_both_legs():
    dense = [Item("a", 0.9), Item("b", 0.8)]
    sparse = [Item("b", 5.0), Item("c", 4.0)]
    scores = rrf({"dense": dense, "sparse": sparse}, k=60.0)
    assert max(scores, key=scores.get) == "b"
    assert set(scores) == {"a", "b", "c"}


def test_rrf_monotonic_in_rank():
    # a shared item ranked higher in both legs beats one ranked lower
    dense = [Item("x", 0.9), Item("y", 0.8)]
    sparse = [Item("x", 3.0), Item("y", 2.0)]
    scores = rrf({"dense": dense, "sparse": sparse}, k=60.0)
    assert scores["x"] > scores["y"]


def test_weighted_normalizes_scales():
    # dense scores tiny, sparse scores huge; min-max makes them comparable
    dense = [Item("a", 0.01), Item("b", 0.02)]
    sparse = [Item("a", 1000.0), Item("b", 1001.0)]
    scores = weighted({"dense": dense, "sparse": sparse}, {"dense": 1.0, "sparse": 1.0})
    # both legs agree b > a, so b must win
    assert scores["b"] > scores["a"]


def test_dbsf_uses_standard_scores():
    dense = [Item("a", 1.0), Item("b", 2.0)]
    sparse = [Item("a", 10.0), Item("b", 11.0)]
    scores = dbsf({"dense": dense, "sparse": sparse}, {"dense": 1.0, "sparse": 1.0})
    assert scores["b"] > scores["a"]


def test_fuse_dispatch():
    dense = [Item("a", 0.9)]
    sparse = [Item("a", 1.0)]
    assert fuse({"dense": dense, "sparse": sparse}, method="rrf")["a"] > 0
    assert fuse({"dense": dense, "sparse": sparse}, method="weighted")["a"] > 0


def test_sort_by_fused_attaches_diagnostics():
    dense = [Item("a", 0.9), Item("b", 0.8)]
    sparse = [Item("b", 5.0), Item("c", 4.0)]
    fused = rrf({"dense": dense, "sparse": sparse}, k=60.0)
    out = sort_by_fused({"dense": dense, "sparse": sparse}, fused, top_k=3)
    assert len(out) == 3
    top = out[0]
    assert top.passage_id == "b"
    assert top.dense_rank == 2 and top.sparse_rank == 1
    assert top.dense_score == 0.8 and top.sparse_score == 5.0
