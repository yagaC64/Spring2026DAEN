# DuckDB + Streamlit Baseline Notes

## Assumptions

- The baseline is local/internal only and does not replace the current GitHub Pages public dashboard.
- The baseline rebuilds from current curated outputs rather than from raw source feeds.
- The most stable current curated inputs are municipio scoring outputs, priority actions, station summaries, alert summaries, and terrain outputs when present.
- Municipio joins are handled through normalized slug keys derived from current output names.

## Open Questions

- Which current outputs should be treated as the long-term canonical curated inputs for future database loading?
- Should future baseline map views move from centroid-style latitude/longitude summaries to polygon-aware geospatial layers?
- Should a later iteration add a stronger dependency/packaging model for the entire repo instead of only this local workbench?
- Which additional scoring-support outputs should be promoted next into the baseline schema after the age overlay: transport/no-vehicle, housing fragility, income capacity, or other social indicators?

## Known Gaps

- The workbench is intentionally small and does not model every notebook output.
- GeoJSON sources are inventoried for future extensions but are not yet loaded into a spatial database schema.
- The Streamlit app is a local workbench shell and not a production deployment target.
