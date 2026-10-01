import json
from koml_shadow_mode.cli import workflow
from koml_shadow_mode.report import render

def test_report_matches_ground_truth_exact(fixture_dir):
    result = json.loads(render(workflow(fixture_dir), "json"))
    expected = json.loads((fixture_dir / "expectations.json").read_text())
    assert result["metrics"] == expected["metrics"]

def test_report_zero_false_positives(fixture_dir):
    result = json.loads(render(workflow(fixture_dir), "json"))
    detected = {r["id"] for r in result["rows"] if r["disagrees"]}
    planted = {f"fixture-{i:03d}" for i in range(100, 200)}
    assert detected - planted == set()
    assert planted - detected == set()

def test_report_carries_provenance_banner(fixture_dir):
    for format in ("md", "json"):
        text = render(workflow(fixture_dir), format)
        assert "DATA PROVENANCE" in text
        assert "records.jsonl" in text
        assert "synthetic" in text.lower()

def test_hypothetical_figures_labelled(fixture_dir):
    for format in ("md", "json"):
        text = render(workflow(fixture_dir), format)
        assert "hypothetical" in text
        assert "Unmeasured" in text
        assert "baseline" in text

def test_no_em_dashes_in_outputs(fixture_dir):
    for format in ("md", "json"):
        assert chr(0x2014) not in render(workflow(fixture_dir), format)

def test_mixed_provenance(fixture_dir):
    path = fixture_dir / "records.jsonl"
    lines = path.read_text().splitlines()
    record = json.loads(lines[1]); record["synthetic"] = False
    lines[1] = json.dumps(record)
    path.write_text("\n".join(lines), encoding="utf-8")
    data = json.loads(render(workflow(fixture_dir), "json"))
    assert data["metrics"]["real_records"] == 1
    assert data["provenance"]["real_inputs_user_declared"] == ["records.jsonl"]
