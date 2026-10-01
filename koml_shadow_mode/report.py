"""Reports explicitly distinguish provenance and hypothetical decisions."""
import json


def safe(text):
    return text.replace(chr(0x2014), "-")


def render(result, format="md"):
    real = sorted({r["source"] for r in result["rows"] if not r["synthetic"]})
    synthetic = sorted({r["source"] for r in result["rows"] if r["synthetic"]})
    provenance = {"banner": "DATA PROVENANCE: synthetic fixtures and user-declared real inputs are distinguished below.",
                  "synthetic_inputs": synthetic, "real_inputs_user_declared": real,
                  "real_input_note": "Real means synthetic:false as declared by the operator; authorship is not independently verified."}
    data = {**result, "provenance": provenance}
    if format == "json":
        return safe(json.dumps(data, ensure_ascii=True, indent=2, sort_keys=True) + "\n")
    lines = ["# KOML Shadow Mode report", "", provenance["banner"],
             "Synthetic inputs: " + (", ".join(synthetic) or "none"),
             "Real inputs (user-declared): " + (", ".join(real) or "none"),
             provenance["real_input_note"], "", result["hypothetical"], result["savings"], "",
             "## Computed figures", "", "| Figure | Value |", "| --- | ---: |"]
    lines += [f"| {key} | {value} |" for key, value in sorted(result["metrics"].items())]
    lines += ["", "## Per-record evidence", "", "Each JSON row includes source file and line. Costs are input cost units, not money saved.", "", "```json",
              safe(json.dumps(result["rows"], ensure_ascii=True, indent=2, sort_keys=True)), "```", ""]
    return safe("\n".join(lines))
