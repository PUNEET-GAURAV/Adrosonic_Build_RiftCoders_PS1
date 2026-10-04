from trustrag.adapters.memory_cache import MemoryCache
from trustrag.core.cache_key import cache_key


def test_cache_key_includes_version():
    k1 = cache_key("how to boil an egg", "hybrid", {"category": ["NUMERIC"]}, ["public"], 1)
    k2 = cache_key("how to boil an egg", "hybrid", {"category": ["NUMERIC"]}, ["public"], 2)
    assert k1 != k2  # index version changes the key (invalidation)


def test_cache_key_includes_groups_and_filters():
    base = cache_key("q", "hybrid", {}, [], 0)
    assert cache_key("q", "hybrid", {}, ["admin"], 0) != base
    assert cache_key("q", "hybrid", {"source": ["x"]}, [], 0) != base


def test_lru_eviction():
    c = MemoryCache(maxsize=2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")  # touch a
    c.put("c", 3)
    assert c.get("a") == 1
    assert c.get("b") is None  # evicted
    assert c.get("c") == 3


def test_semantic_hit_and_miss():
    c = MemoryCache(maxsize=10, semantic_threshold=0.9)
    c.put("k", "value")
    c.put_semantic([1.0, 0.0], "k")
    assert c.get_semantic([0.99, 0.01]) == "value"
    assert c.get_semantic([0.0, 1.0]) is None
