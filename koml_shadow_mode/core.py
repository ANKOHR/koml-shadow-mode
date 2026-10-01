"""Pure deterministic rules. Costs are supplied observations, never savings."""
from datetime import date


class SchemaError(ValueError):
    """An explicit input field violates the schema."""


def validate(record, seen):
    if not isinstance(record, dict):
        raise SchemaError("record: expected object")
    required = {"id", "synthetic", "date", "as_of", "score", "threshold", "actual", "cost"}
    if set(record) != required:
        raise SchemaError(f"fields: missing {sorted(required - set(record))}; unknown {sorted(set(record) - required)}")
    identifier = record["id"]
    if not isinstance(identifier, str) or not identifier or len(identifier) > 10000:
        raise SchemaError("id: expected 1 to 10000 characters")
    if identifier in seen:
        raise SchemaError(f"id: duplicate {identifier!r}")
    if type(record["synthetic"]) is not bool:
        raise SchemaError("synthetic: expected boolean")
    for field in ("score", "threshold", "cost"):
        value = record[field]
        if type(value) is not int or not 0 <= value <= 10**12:
            raise SchemaError(f"{field}: expected integer from 0 to 1000000000000")
    if record["actual"] not in ("approve", "reject"):
        raise SchemaError("actual: expected approve or reject")
    for field in ("date", "as_of"):
        try:
            value = record[field]
            if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
                raise ValueError()
        except (ValueError, TypeError):
            raise SchemaError(f"{field}: expected ISO YYYY-MM-DD") from None
    if record["date"] > record["as_of"]:
        raise SchemaError("date: future relative to explicit as_of")
    seen.add(identifier)
    return dict(record)


def simulate(record):
    """Hypothetical rule choice; never invokes an action."""
    return "approve" if record["score"] >= record["threshold"] else "reject"


def compare(records):
    seen = set()
    rows = []
    for record in records:
        r = validate(record, seen)
        choice = simulate(r)
        rows.append({**r, "shadow": choice, "disagrees": choice != r["actual"]})
    rows.sort(key=lambda r: r["id"])
    counts = {"records": len(rows), "agreements": 0, "disagreements": 0,
              "shadow_approve_actual_reject": 0, "shadow_reject_actual_approve": 0,
              "observed_cost_units": 0, "synthetic_records": 0, "real_records": 0}
    for r in rows:
        counts["disagreements" if r["disagrees"] else "agreements"] += 1
        counts["synthetic_records" if r["synthetic"] else "real_records"] += 1
        counts["observed_cost_units"] += r["cost"]
        if r["disagrees"]:
            counts[f"shadow_{r['shadow']}_actual_{r['actual']}"] += 1
    return {"schema_version": 1, "metrics": counts, "rows": rows,
            "hypothetical": "Shadow choices are hypothetical rule simulations, not predictions or executed actions.",
            "savings": "Unmeasured: time and money savings are not computed without a measured baseline."}
