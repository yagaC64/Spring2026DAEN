from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.factors.social_adjustments import (
    age_adjustment_enabled,
    age_adjustment_variable_map,
    apply_age_adjustment,
    build_adjustment_factor_reference,
    build_municipio_adjustment_table,
    load_social_adjustment_spec,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_social_adjustment_spec_exposes_expected_age_variables() -> None:
    spec = load_social_adjustment_spec(REPO_ROOT)
    variables = age_adjustment_variable_map(spec)

    assert age_adjustment_enabled(spec) is True
    assert variables["male_under5"] == "B01001_003E"
    assert variables["female_85_up"] == "B01001_049E"


def test_apply_age_adjustment_builds_points_and_adjusted_score() -> None:
    spec = load_social_adjustment_spec(REPO_ROOT)
    frame = pd.DataFrame(
        [
            {
                "municipio": "San Juan",
                "municipio_key": "san_juan",
                "population": 10000,
                "male_under5": 250,
                "female_under5": 240,
                "male_65_66": 120,
                "male_67_69": 110,
                "male_70_74": 140,
                "male_75_79": 100,
                "male_80_84": 70,
                "male_85_up": 40,
                "female_65_66": 130,
                "female_67_69": 120,
                "female_70_74": 150,
                "female_75_79": 115,
                "female_80_84": 95,
                "female_85_up": 60,
                "vulnerability_score_base": 58.8,
            },
            {
                "municipio": "Ponce",
                "municipio_key": "ponce",
                "population": 10000,
                "male_under5": 120,
                "female_under5": 110,
                "male_65_66": 70,
                "male_67_69": 65,
                "male_70_74": 75,
                "male_75_79": 45,
                "male_80_84": 30,
                "male_85_up": 15,
                "female_65_66": 80,
                "female_67_69": 70,
                "female_70_74": 85,
                "female_75_79": 55,
                "female_80_84": 35,
                "female_85_up": 20,
                "vulnerability_score_base": 52.1,
            },
        ]
    )

    adjusted = apply_age_adjustment(
        frame,
        spec,
        base_score_column="vulnerability_score_base",
        adjusted_score_column="vulnerability_score_adjusted",
    )

    assert "score_age_vulnerability" in adjusted.columns
    assert "age_adjustment_points" in adjusted.columns
    assert adjusted["age_adjustment_points"].max() > adjusted["age_adjustment_points"].min()
    assert (adjusted["vulnerability_score_adjusted"] >= adjusted["vulnerability_score_base"]).all()

    municipio_table = build_municipio_adjustment_table(adjusted, spec)
    assert "elderly_65_plus_rate" in municipio_table.columns
    assert "vulnerability_score_adjusted" in municipio_table.columns

    reference = build_adjustment_factor_reference(spec)
    assert {"adjustment_key", "group_key", "max_adjustment_points"}.issubset(reference.columns)
