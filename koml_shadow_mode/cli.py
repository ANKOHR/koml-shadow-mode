"""Local file CLI. No network, model calls, or action execution."""
import argparse
import json
import os
from pathlib import Path
import tempfile
from .core import SchemaError, compare
from .fixtures import generate
from .report import render, safe


class InputError(ValueError):
    pass


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate JSON field {key}")
        obj[key] = value
    return obj


def validate_state(result):
    """Refuse stale or edited totals rather than presenting them as computed."""
    fields = {"id", "synthetic", "date", "as_of", "score", "threshold", "actual", "cost"}
    rows = result["rows"]
    inputs = [{key: row[key] for key in fields} for row in rows]
    expected = compare(inputs)
    if result["schema_version"] != 1 or result["metrics"] != expected["metrics"]:
        raise ValueError("schema_version or metrics do not reconcile with rows")
    if result["hypothetical"] != expected["hypothetical"] or result["savings"] != expected["savings"]:
        raise ValueError("honesty labels were modified")
    for row, computed in zip(rows, expected["rows"]):
        if {key: value for key, value in row.items() if key not in ("source", "line")} != computed:
            raise ValueError("row calculations or ordering do not reconcile")
        if not isinstance(row["source"], str) or type(row["line"]) is not int or row["line"] < 1:
            raise ValueError("source or line is invalid")
    return result


def read_records(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise InputError(f"MissingInput: {directory}: use --input with an existing directory")
    records, sources = [], []
    # Only records.jsonl or *.records.jsonl are supported; metadata is not input.
    paths = sorted(set(directory.glob("*.records.jsonl")) | set(directory.glob("records.jsonl")))
    unexpected = [p.name for p in directory.iterdir() if p.is_file() and p.suffix.lower() in (".json", ".jsonl", ".csv", ".yaml", ".yml") and p not in paths and p.name != "expectations.json"]
    if unexpected:
        raise InputError(f"SchemaError: {directory}: line 1: unsupported input file {sorted(unexpected)[0]}; use records.jsonl or *.records.jsonl")
    for path in paths:
        try:
            with path.open(encoding="utf-8") as handle:
                for line_no, line in enumerate(handle, 1):
                    if not line.strip() or line.startswith("#"):
                        continue
                    try:
                        records.append(json.loads(line, object_pairs_hook=unique_object))
                    except json.JSONDecodeError as exc:
                        raise InputError(f"ParseError: {path}: line {line_no}, column {exc.colno}: {exc.msg}") from None
                    except ValueError as exc:
                        raise InputError(f"ParseError: {path}: line {line_no}: {exc}") from None
                    sources.append((path.name, line_no))
        except UnicodeError:
            raise InputError(f"ParseError: {path}: line 1: expected UTF-8") from None
    # Validate one at a time to retain exact source location, including duplicates.
    from .core import validate
    seen = set()
    for record, (name, line) in zip(records, sources):
        try:
            validate(record, seen)
        except SchemaError as exc:
            raise InputError(f"SchemaError: {name}: line {line}: {exc}") from None
    return records, sources


def workflow(directory):
    records, sources = read_records(directory)
    result = compare(records)
    locations = {r["id"]: loc for r, loc in zip(records, sources)}
    for row in result["rows"]:
        row["source"], row["line"] = locations[row["id"]]
    return result


def atomic_write(path, content):
    path = Path(path)
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        os.replace(temporary, path)
    except OSError as exc:
        raise InputError(f"WriteError: {path}: {exc}") from None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Simulate hypothetical decisions locally and compare recorded choices.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("fixtures", help="Generate 200 labelled synthetic records", epilog="Example: ksm2 fixtures --out demo")
    p.add_argument("--out", required=True)
    for name, help_text in (("run", "Compute comparisons and store results"), ("simulate", "Print hypothetical rule choices without executing them"), ("compare", "Compare shadow choices with actual recorded choices")):
        p = sub.add_parser(name, help=help_text, description=help_text, epilog=f"Example: ksm2 {name} --input demo")
        p.add_argument("--input", required=True)
        if name == "run":
            p.add_argument("--state", default=".ksm2/result.json")
    p = sub.add_parser("report", help="Render computed results with provenance", epilog="Example: ksm2 report --format md")
    p.add_argument("--format", choices=("md", "json"), default="md")
    p.add_argument("--state", default=".ksm2/result.json")
    p.add_argument("--out")
    args = parser.parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("Generated 200 SYNTHETIC records. Shadow decisions are hypothetical.")
        elif args.command == "report":
            path = Path(args.state)
            if not path.is_file():
                raise InputError(f"MissingInput: {path}: run ksm2 run --input <dir> first")
            try:
                result = validate_state(json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object))
                output = render(result, args.format)
            except (ValueError, KeyError, TypeError, AttributeError) as exc:
                raise InputError(f"SchemaError: {path}: line 1: invalid computed state: {exc}") from None
            if args.out:
                atomic_write(args.out, output)
            else:
                print(output, end="")
        else:
            result = workflow(args.input)
            if args.command == "run":
                atomic_write(args.state, json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
                print(f"Computed {result['metrics']['records']} records. Shadow choices are hypothetical; savings unmeasured. State: {safe(args.state)}")
            elif args.command == "simulate":
                print(render(result, "json"), end="")
            else:
                print(render(result, "json"), end="")
        return 0
    except (InputError, OSError) as exc:
        print(safe(str(exc)), file=__import__("sys").stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
