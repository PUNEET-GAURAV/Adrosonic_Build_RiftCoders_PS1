from trustrag.retrieval.filters import matches

META = {
    "category": "NUMERIC",
    "source": "msmarco",
    "topic": "food",
    "acl_groups": ["public"],
    "doc_version": 1,
    "ingested_at": "2026-10-01T12:00:00Z",
}


def test_no_filter_matches():
    assert matches(META) is True


def test_category_match():
    assert matches(META, category=["NUMERIC"]) is True
    assert matches(META, category=["DESCRIPTION"]) is False


def test_acl_overlap():
    assert matches(META, acl_groups=["public"]) is True
    assert matches(META, acl_groups=["admin"]) is False
    assert matches(META, acl_groups=["public", "admin"]) is True


def test_date_range():
    assert matches(META, ingested_after="2026-10-01T00:00:00Z") is True
    assert matches(META, ingested_after="2026-10-02T00:00:00Z") is False
    assert matches(META, ingested_before="2026-10-01T00:00:00Z") is False
