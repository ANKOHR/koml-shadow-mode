import json
import subprocess
import sys
import time
from pathlib import Path
import pytest
from koml_shadow_mode.cli import main, workflow


def test_run_completes_on_fixture(fixture_dir, monkeypatch):
    monkeypatch.chdir(fixture_dir)
    start = time.perf_counter()
    assert main(["run", "--input", str(fixture_dir)]) == 0
    assert main(["report", "--format", "md", "--out", "report.md"]) == 0
    assert time.perf_counter() - start < 5


def test_empty_input_renders_without_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["run", "--input", str(tmp_path)]) == 0
    assert main(["report", "--format", "json"]) == 0
    output = capsys.readouterr().out
    assert '"records": 0' in output
    assert "Traceback" not in output


def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "records.jsonl").write_text('# SYNTHETIC\n{bad}\n')
    assert main(["run", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "ParseError" in error and "records.jsonl" in error and "line 2" in error


def test_determinism_byte_identical(fixture_dir, monkeypatch):
    monkeypatch.chdir(fixture_dir)
    outputs = []
    for _ in range(2):
        assert main(["run", "--input", str(fixture_dir)]) == 0
        assert main(["report", "--format", "json", "--out", "out.txt"]) == 0
        outputs.append((Path(".ksm2/result.json").read_bytes(), Path("out.txt").read_bytes()))
    assert outputs[0] == outputs[1]


def test_cli_smoke_all_subcommands(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["fixtures", "--out", "demo"]) == 0
    for command in ("run", "simulate", "compare"):
        assert main([command, "--input", "demo"]) == 0
    for format in ("md", "json"):
        assert main(["report", "--format", format]) == 0
    for command in ("fixtures", "run", "report", "simulate", "compare"):
        with pytest.raises(SystemExit) as exc:
            main([command, "--help"])
        assert exc.value.code == 0
    assert chr(0x2014) not in capsys.readouterr().out


def test_handles_unicode_and_long_inputs(fixture_dir):
    path = fixture_dir / "records.jsonl"
    r = json.loads(path.read_text().splitlines()[1])
    r["id"] = "Ã¦Â¼Â¢Ã¥Â­â€” cafÃƒÂ© C:\\Users\\henry\\" + "x" * 9000 + chr(0x2014)
    path.write_text(json.dumps(r, ensure_ascii=False) + "\n", encoding="utf-8")
    from koml_shadow_mode.report import render
    result = json.loads(render(workflow(fixture_dir), "json"))
    assert result["rows"][0]["id"] == r["id"]


def test_report_write_failure_no_partial_files(fixture_dir, monkeypatch, capsys):
    monkeypatch.chdir(fixture_dir)
    assert main(["run", "--input", "."]) == 0
    path = fixture_dir / "blocked"
    path.write_text("preserve")
    before = set(fixture_dir.iterdir())
    assert main(["report", "--out", "blocked/output.md"]) == 2
    assert "WriteError" in capsys.readouterr().err
    assert set(fixture_dir.iterdir()) == before
    assert path.read_text() == "preserve"


def test_missing_input(tmp_path, capsys):
    assert main(["run", "--input", str(tmp_path / "absent")]) == 2
    assert "MissingInput" in capsys.readouterr().err


def test_five_handwritten_records():
    records = Path(__file__).parents[1] / "examples" / "tiny"
    result = workflow(records)
    assert result["metrics"]["records"] == 5
    assert result["metrics"]["agreements"] == 3
    assert result["metrics"]["disagreements"] == 2


def test_installed_cli_entrypoint():
    import shutil
    import sysconfig
    executable = shutil.which("ksm2")
    if executable is None:
        scripts = Path(sysconfig.get_path("scripts", scheme="nt_user" if sys.platform == "win32" else "posix_user"))
        executable = str(scripts / ("ksm2.exe" if sys.platform == "win32" else "ksm2"))
    result = subprocess.run([executable, "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "simulate" in result.stdout


@pytest.mark.parametrize("contents", ['null', '{bad}', '{"rows": []}', '[]'])
def test_corrupted_state_named_error(tmp_path, capsys, contents):
    state = tmp_path / "state.json"
    state.write_text(contents)
    assert main(["report", "--state", str(state)]) == 2
    assert "SchemaError" in capsys.readouterr().err


def test_edited_totals_refused(fixture_dir, monkeypatch, capsys):
    monkeypatch.chdir(fixture_dir)
    assert main(["run", "--input", "."]) == 0
    state = Path(".ksm2/result.json")
    result = json.loads(state.read_text())
    result["metrics"]["agreements"] = 999
    state.write_text(json.dumps(result))
    assert main(["report"]) == 2
    assert "reconcile" in capsys.readouterr().err


def test_duplicate_json_fields(tmp_path, capsys):
    (tmp_path / "records.jsonl").write_text('{"id":"a","id":"b"}')
    assert main(["run", "--input", str(tmp_path)]) == 2
    assert "duplicate JSON field" in capsys.readouterr().err


def test_schema_error_has_line(fixture_dir, capsys):
    path = fixture_dir / "records.jsonl"
    record = json.loads(path.read_text().splitlines()[1])
    record["cost"] = -1
    path.write_text("# SYNTHETIC\n" + json.dumps(record))
    assert main(["run", "--input", str(fixture_dir)]) == 2
    err = capsys.readouterr().err
    assert "SchemaError" in err and "cost" in err and "line 2" in err
