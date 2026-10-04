from trustrag.core.text import cosine_sim, fnv1a32, normalize, term_frequencies, tokenize


def test_tokenize_lowercases_and_splits():
    assert tokenize("Hello, WORLD 123!") == ["hello", "world", "123"]


def test_hash_stable_and_distinct():
    assert fnv1a32("hello") == fnv1a32("hello")
    assert fnv1a32("hello") != fnv1a32("world")


def test_term_frequencies_counts():
    tf = term_frequencies("cat cat dog")
    assert tf[fnv1a32("cat")] == 2
    assert tf[fnv1a32("dog")] == 1


def test_cosine():
    assert abs(cosine_sim([1, 0], [1, 0]) - 1.0) < 1e-9
    assert abs(cosine_sim([1, 0], [0, 1])) < 1e-9
    assert cosine_sim([], [1]) == 0.0


def test_normalize():
    v = normalize([3, 4])
    assert abs(v[0] - 0.6) < 1e-9
    assert abs(v[1] - 0.8) < 1e-9
