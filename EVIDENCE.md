# Build evidence

Measured locally on 2026-10-01 using Python 3.12.10, CPU only.

The installed ksm2 launcher ran fixtures, run and report in three fresh subprocesses on 200 synthetic records in 0.574646 seconds total. Output was captured, with no tracebacks and the DATA PROVENANCE banner present. This is a measured local duration, not a forecast for other machines. No time or money saved was measured.

Independent expectations: 200 records, 100 agreements, 100 disagreements, 50 shadow approve / actual reject, 50 shadow reject / actual approve, 2000 supplied cost units, 200 synthetic records, zero real records. Exact equality and planted ID sets are tested. The reported disagreement set has zero false positives and zero missed planted cases. All 38 pytest cases pass, including corrupted actual choices, corrupted stored totals, empty input, named parse/schema errors, duplicates, invalid numbers and dates, Unicode, long IDs, deterministic bytes and atomic write failure.

The tiny hand-written synthetic input gives three agreements and two disagreements out of five. No Henry real data was used. Real decision quality, daily use, savings and operational error rate remain unmeasured. The two-week verdict is pending in VERDICT.md.
