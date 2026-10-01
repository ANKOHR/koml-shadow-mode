"""Synthetic fixtures with arithmetic expectations independent of core logic.

No random generator is used; seed is not applicable.
"""
import json
from pathlib import Path


def generate(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    records = []
    # Four groups of 50: matching approvals, matching rejections,
    # shadow approval disagreement, shadow rejection disagreement.
    for i in range(200):
        group = i // 50
        records.append({"id": f"fixture-{i:03d}", "synthetic": True,
                        "date": "2026-09-01", "as_of": "2026-09-30",
                        "score": 80 if group in (0, 2) else 20, "threshold": 50,
                        "actual": "approve" if group in (0, 3) else "reject", "cost": 10})
    with (out / "records.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("# SYNTHETIC: planted labelled decision records\n")
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    expectations = {"synthetic": True, "label": "SYNTHETIC hand-computed ground truth",
                    "arithmetic": "4 groups x 50; 2 matching groups; 200 x 10 cost units",
                    "metrics": {"records": 200, "agreements": 100, "disagreements": 100,
                                "shadow_approve_actual_reject": 50, "shadow_reject_actual_approve": 50,
                                "observed_cost_units": 2000, "synthetic_records": 200, "real_records": 0},
                    "disagreement_ids": [f"fixture-{i:03d}" for i in range(100, 200)]}
    (out / "expectations.json").write_text(json.dumps(expectations, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return records
