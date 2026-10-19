# Measured records

Machine-readable output behind the report's Tables II and D1, kept so the numbers quoted there can
be checked without re-running anything.

| File | Produced by | Backs |
|---|---|---|
| `dose_series.json` | `python atomfind/dose_series.py --json …` | report Table II — the dose series and the deconvolve-then-peak-pick head-to-head |
| `noise_sweep.json` | `python atomfind/noise_sweep.py --json …` | report Table D1 — the injected-noise ladder |

Each holds the full `finder_report` dict per condition, so precision, per-species recall, the
oxygen split and the detection counts are all recoverable, not just the columns that made it
into the tables.
