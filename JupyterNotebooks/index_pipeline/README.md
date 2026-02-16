# Index Pipeline Notebook Stack

This pipeline is organized by stage and discipline and is intended to be run in numeric order.

## Stage Order

1. `01_ingest_hazard/01_ingest_flood_hazard_feeds.ipynb`
2. `01_ingest_hazard/02_ingest_earthquake_hazard_feeds.ipynb`
3. `02_feature_engineering/10_build_exposure_vulnerability_features.ipynb`
4. `02_feature_engineering/20_build_municipio_hazard_features.ipynb`
5. `03_scoring/30_score_operational_indices.ipynb`
6. `04_validation/40_validate_index_outputs.ipynb`
7. `05_products/50_generate_priority_products.ipynb`

## Output Root

`JupyterNotebooks/outputs/index_pipeline/`

## Notes

- Stage separation is intentional: ingest, feature engineering, scoring, validation, and product generation are isolated for reproducibility.
- Each stage writes explicit artifacts consumed by the next stage.
- This stack implements the `findings_to_index_implementation_playbook.md` design in executable notebook form.
