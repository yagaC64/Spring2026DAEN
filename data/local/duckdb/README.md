# DuckDB Local Baseline

This folder is reserved for the local DuckDB workbench and related local build artifacts.

Expected local files:

- `spring2026daen_baseline.duckdb`
- `duckdb_baseline_build_summary.json`

Build command:

```bash
python scripts/build_duckdb_baseline.py
```

This folder is intentionally local-first and should not be used as the public dashboard source of truth.
