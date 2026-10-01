# KOML Shadow Mode

`ksm2` simulates a deterministic approval rule and compares its hypothetical choices with recorded actual choices. It never executes a decision. CPU only, Python standard library at runtime, local files only, no network or model calls.

## Hypothesis and acceptance

An explicit tested rule and record-level evidence can make shadow comparison trustworthy. The acceptance fixture contains 200 synthetic records with planted disagreement IDs. Every figure must equal independent arithmetic, no planted disagreements may be missed, no matching records may be flagged, and the full CLI demo must complete in under five seconds. This tests implementation correctness, not whether the rule makes good decisions in real operations.

## Quickstart

Python 3.10 or newer, setuptools 68 or newer, and pytest for tests. With these already installed, installation needs no network:

```powershell
python -m venv --system-site-packages .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --no-index --no-build-isolation --no-deps --disable-pip-version-check -e .
ksm2 fixtures --out demo
ksm2 run --input demo
ksm2 report --format md
python -m pytest -q
```

On Windows, user-level Python installs can put scripts outside PATH. Activating the virtual environment above exposes `ksm2`. `python -m koml_shadow_mode.cli` also accepts exactly the same arguments. PowerShell 7 supports the requested chained demo:

```powershell
ksm2 fixtures --out demo && ksm2 run --input demo && ksm2 report --format md
```

For the smallest hand-written version:

```powershell
ksm2 run --input examples/tiny
ksm2 report --format json
```

The five synthetic examples have three agreements, two disagreements, and 50 supplied cost units. Trial results from Henry's real operations are not shipped.

## Input format reference

An input directory contains `records.jsonl` or files ending in `.records.jsonl`. Each nonblank, noncomment line is one JSON object. UTF-8 is required. Lines beginning with `#` are comments. Files are read in sorted order. Other JSON, JSONL, CSV, or YAML data files are rejected with a schema error, except `expectations.json`, which is fixture metadata and never drives calculations. No data file is silently parsed as a different format.

| Field | Required meaning and validation |
| --- | --- |
| id | Unique across all files; string of 1 to 10000 characters |
| synthetic | Boolean; true for invented fixtures, false for operator-declared real data |
| date | Observation date, exact ISO YYYY-MM-DD |
| as_of | Explicit evaluation cutoff date; date must be on or before this cutoff |
| score | Supplied integer from 0 through 1000000000000 |
| threshold | Supplied integer in the same range |
| actual | Recorded choice: approve or reject |
| cost | Supplied nonnegative integer cost units in the same range; not currency or savings |

No extra or missing fields are accepted. Booleans are not integers. Negative values, floats, NaN, duplicate JSON keys, duplicate IDs, invalid dates, and oversized IDs are rejected. Future means after the supplied `as_of`, never after a nondeterministic system clock. The operator must supply a truthful cutoff for real records. Unicode and Windows path text in IDs are supported; JSON backslashes must be escaped normally.

```json
{"id":"Henry-entered-001","synthetic":false,"date":"2026-09-30","as_of":"2026-09-30","score":60,"threshold":50,"actual":"reject","cost":0}
```

The example above is an illustrative schema example, not shipped real evidence. Replace it with actual hand-entered observations and mark those `synthetic:false`. If cost was not measured, use zero only when zero is a truthful observed value; this version requires a supplied cost observation and does not impute missing costs.

The hypothetical rule is `approve` when `score >= threshold`, otherwise `reject`. Equality is approval. A disagreement means the shadow choice differs from `actual`; neither choice is automatically the correct choice. The two directional counts sum to disagreements. Agreements plus disagreements equal records. Synthetic plus real records equal records. Cost totals are exact integer sums of supplied observations. Fixture false positives mean flagged agreements, not real-world decision accuracy.

## Subcommand catalogue

Every subcommand provides `--help` and an example.

| Command | Example | Behavior |
| --- | --- | --- |
| fixtures | `ksm2 fixtures --out demo` | Generate 200 labelled synthetic records and independent expectations; overwrites those two fixture files |
| run | `ksm2 run --input demo --state .ksm2/result.json` | Validate, simulate, compare and atomically store computed state |
| simulate | `ksm2 simulate --input demo` | Print hypothetical choices, input evidence and comparison context as JSON; executes no action and stores nothing |
| compare | `ksm2 compare --input demo` | Print agreement and directional disagreement figures plus per-record evidence as JSON; stores nothing |
| report | `ksm2 report --format md --out report.md` | Render the latest stored state; formats md and json; omit --out for stdout |

`report --state <path>` selects a different result. State is a snapshot, so rerun after changing inputs. Reports revalidate rows and reconcile totals before rendering. File writes use a same-directory temporary file and atomic replacement; failed writes leave no partial output and preserve existing targets. Exit code 0 means success, 2 means input, parse, schema, usage, or write failure. Errors name the source file and line for record problems. Missing inputs include a usage hint. An empty directory is valid and renders zeros.

## Architecture

```text
fixtures.py -> labelled JSONL + independent expectations.json
local JSONL -> cli.py parsing and file/line validation
            -> core.py pure validation, rule simulation, comparison
            -> .ksm2/result.json (atomic snapshot)
            -> report.py reconciliation and provenance -> Markdown / JSON
```

There are no action adapters. The core has no I/O. Runtime dependencies are empty. JSON keys, record order, input order, and newlines are deterministic; no random seed is needed because fixtures use four arithmetic groups. Identical inputs, source names and options produce byte-identical outputs. Reports contain no wall-clock timestamps or runtime estimates. Runtime is measured separately as build evidence.

## Honesty boundary and fixture labels

Shadow decisions are hypothetical in code, CLI output and both report formats. Input observations and exact comparisons are computed, not predicted. No time or money savings is claimed: without measured baseline data the tool labels savings unmeasured and does not calculate them. Supplied cost units are observations, not savings.

Provenance banners list synthetic input files and user-declared real input files separately. Mixed files may appear in both lists. `synthetic:false` is an operator declaration, not verification of Henry's authorship. No real Henry data is bundled. Every fixture JSONL has a SYNTHETIC header and every record has `synthetic:true`; JSON metadata carries `synthetic:true` and a SYNTHETIC label because JSON does not allow comments. Reports retain file names and line numbers for every record.

JSON output escapes Unicode while preserving exact values when decoded, so it is portable across Windows consoles. Markdown source labels replace U+2014 with a plain hyphen; embedded evidence JSON preserves that character as a Unicode escape. Generated outputs contain no literal U+2014 characters.

## Failure modes and limits

Malformed JSON produces ParseError with file and line. Unsupported formats or schema drift produce SchemaError with the offending file or field. Missing directories or results produce MissingInput. Unwritable output paths produce WriteError. Invalid input fails the whole run and never drops individual records. A previous valid state remains after a failed run, so an operator must check the exit status before using a previous report. Invalid or manually altered result totals are refused.

This is a two-choice supplied-score rule, not a model of unrestricted agent behavior. It cannot judge whether an actual decision was justified, verify truthfulness of user inputs, estimate causal impact, or prove the rule's operational value. State and input files must be managed as trusted local artifacts. The report includes IDs, so avoid including secrets in IDs. Atomic replacement is not a multi-process locking protocol.

## Evidence and two-week improvement hook

See EVIDENCE.md for measured build checks, LESSONS.md for findings and VERDICT.md for the evidence gate. The synthetic metric is exact agreement with independent planted calculations. The real-use metric is discrepancy rate of reported shadow choices and comparison counts against a hand-checked sample, plus daily run count to establish use. Log all runs and sampled discrepancies locally, including sample size and cutoff, for two weeks starting with the first real run. Trial records remain private and are not shipped.

After that window, calculate discrepancy rate as erroneous sampled records divided by sampled records. Do not report an error rate for a zero-size sample. If error exceeds 10 percent, fix the top observed failure cause and repeat validation, or kill with a written reason. If the tool is not used, kill and record why. Record one evidence-based improvement using that observed top cause. No real-use improvement or verdict is claimed before evidence exists.
