from trustrag.core.ids import passage_uuid


def test_deterministic():
    assert passage_uuid("msmarco-train-1-0") == passage_uuid("msmarco-train-1-0")


def test_distinct():
    assert passage_uuid("a") != passage_uuid("b")


def test_well_formed_uuid():
    import uuid

    uuid.UUID(passage_uuid("x"))  # raises if not a valid UUID
