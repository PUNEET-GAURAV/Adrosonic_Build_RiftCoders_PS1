import math

from trustrag.evaluation.metrics import (
    context_precision_from_relevance,
    context_recall_from_relevance,
    hit_at_k,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


def test_precision_recall_hit():
    gold = {"a", "b", "c"}
    retrieved = ["a", "x", "b", "y", "z"]
    assert precision_at_k(gold, retrieved, 5) == 0.4
    assert recall_at_k(gold, retrieved, 5) == 2 / 3
    assert hit_at_k(gold, retrieved, 5) == 1.0
    assert hit_at_k(gold, ["x", "y"], 5) == 0.0


def test_mrr():
    gold = {"b"}
    assert mrr(gold, ["a", "b", "c"]) == 0.5
    assert mrr(gold, ["a", "c"]) == 0.0


def test_ndcg_binary():
    gold = {"a", "c"}
    retrieved = ["a", "x", "c", "y"]
    # DCG = 1/log2(2) + 1/log2(4) = 1 + 0.5 = 1.5 ; IDCG = 1 + 1/log2(3) = 1 + 0.6309
    dcg = 1.0 / math.log2(2) + 1.0 / math.log2(4)
    idcg = 1.0 / math.log2(2) + 1.0 / math.log2(3)
    assert abs(ndcg_at_k(gold, retrieved, 4) - dcg / idcg) < 1e-9


def test_context_precision():
    # relevant at positions 1 and 3
    rel = [True, False, True]
    # relevant seen at 1 -> 1/1 ; at 3 -> 2/3 ; average = (1 + 2/3)/2
    expected = (1.0 + 2 / 3) / 2
    assert abs(context_precision_from_relevance(rel) - expected) < 1e-9
    assert context_precision_from_relevance([False, False]) == 0.0


def test_context_recall():
    assert context_recall_from_relevance([True, False, True], 4) == 0.5
    assert context_recall_from_relevance([], 3) == 0.0
