import json
from koml_shadow_mode.cli import workflow

def test_fixtures_labelled_synthetic(fixture_dir):
    text = (fixture_dir / "records.jsonl").read_text()
    assert text.startswith("# SYNTHETIC")
    assert all(json.loads(line)["synthetic"] is True for line in text.splitlines()[1:])
    assert json.loads((fixture_dir / "expectations.json").read_text())["synthetic"] is True

def test_fixture_ground_truth_matches_hand_computed(fixture_dir):
    expected = json.loads((fixture_dir / "expectations.json").read_text())
    result = workflow(fixture_dir)
    assert result["metrics"] == expected["metrics"]
    assert {r["id"] for r in result["rows"] if r["disagrees"]} == set(expected["disagreement_ids"])
