import pytest
from koml_shadow_mode.core import compare, SchemaError
from koml_shadow_mode.fixtures import generate

@pytest.mark.parametrize("field,value", [("cost", -1), ("score", True), ("threshold", 10**13), ("date", "2026-10-01"), ("actual", "execute"), ("id", "x" * 10001), ("synthetic", "yes"), ("score", float("nan")), ("as_of", None)])
def test_rejects_adversarial_values(tmp_path, field, value):
    r = generate(tmp_path)[0]
    r[field] = value
    with pytest.raises(SchemaError, match=field):
        compare([r])

def test_duplicate_ids(tmp_path):
    r = generate(tmp_path)[0]
    with pytest.raises(SchemaError, match="duplicate"):
        compare([r, r])

def test_boundary_and_empty(tmp_path):
    r = generate(tmp_path)[0]
    r["score"] = r["threshold"]
    assert compare([r])["rows"][0]["shadow"] == "approve"
    assert compare([])["metrics"]["records"] == 0

def test_ground_truth_corruption_changes_output(tmp_path):
    records = generate(tmp_path)
    before = compare(records)
    records[0]["actual"] = "reject"
    after = compare(records)
    assert after["metrics"]["disagreements"] == before["metrics"]["disagreements"] + 1

def test_schema_drift(tmp_path):
    r = generate(tmp_path)[0]
    r["unrecognized"] = 1
    with pytest.raises(SchemaError, match="unrecognized"):
        compare([r])
