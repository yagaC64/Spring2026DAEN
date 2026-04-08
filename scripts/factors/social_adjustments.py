from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml


def find_repo_root(start: Path | None = None) -> Path:
    probe = (start or Path.cwd()).resolve()
    for candidate in [probe, *probe.parents]:
        if (candidate / "README.md").exists() and (candidate / "JupyterNotebooks").exists():
            return candidate
    return probe


def load_social_adjustment_spec(
    repo_root: Path | None = None,
    config_path: Path | None = None,
) -> dict[str, Any]:
    resolved_repo_root = find_repo_root(repo_root)
    resolved_config = config_path or resolved_repo_root / "config" / "social_adjustments_v1.yaml"
    with resolved_config.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def age_adjustment_enabled(spec: dict[str, Any]) -> bool:
    defaults = spec.get("defaults", {})
    age_cfg = spec.get("age_adjustment", {})
    return bool(defaults.get("optional_adjustments_enabled", True) and age_cfg.get("enabled", True))


def age_adjustment_variable_map(spec: dict[str, Any]) -> dict[str, str]:
    variables: dict[str, str] = {}
    for group in spec.get("age_adjustment", {}).get("groups", {}).values():
        variables.update(group.get("acs_variables", {}))
    return variables


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denom = pd.to_numeric(denominator, errors="coerce").replace({0: np.nan})
    result = pd.to_numeric(numerator, errors="coerce") / denom
    return result.replace([np.inf, -np.inf], np.nan)


def robust_score(
    series: pd.Series,
    *,
    lower_quantile: float = 0.05,
    upper_quantile: float = 0.95,
    higher_is_worse: bool = True,
) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    lo = values.quantile(lower_quantile)
    hi = values.quantile(upper_quantile)
    if pd.isna(lo) or pd.isna(hi) or hi <= lo:
        score = pd.Series(np.nan, index=values.index, dtype="float64")
    else:
        score = ((values - lo) / (hi - lo)).clip(0, 1) * 100
    if not higher_is_worse:
        score = 100 - score
    return score


def add_age_support_columns(frame: pd.DataFrame, spec: dict[str, Any]) -> pd.DataFrame:
    out = frame.copy()
    age_cfg = spec.get("age_adjustment", {})
    groups = age_cfg.get("groups", {})

    for group in groups.values():
        for column in group.get("acs_variables", {}):
            if column not in out.columns:
                out[column] = pd.NA
            out[column] = pd.to_numeric(out[column], errors="coerce")

    population = pd.to_numeric(out.get("population"), errors="coerce")
    for group_name, group in groups.items():
        population_column = group.get("population_column")
        rate_column = group.get("rate_column")
        raw_columns = list(group.get("acs_variables", {}).keys())

        if population_column:
            if raw_columns:
                out[population_column] = out[raw_columns].sum(axis=1, min_count=1)
            else:
                out[population_column] = np.nan
        if rate_column and population_column:
            out[rate_column] = _safe_divide(out[population_column], population)

    if "child_under_5" in groups and "elderly_65_plus" in groups:
        out["age_dependency_rate"] = out[[
            groups["child_under_5"].get("rate_column", "child_rate"),
            groups["elderly_65_plus"].get("rate_column", "elderly_65_plus_rate"),
        ]].sum(axis=1, min_count=1)
    return out


def apply_age_adjustment(
    frame: pd.DataFrame,
    spec: dict[str, Any],
    *,
    base_score_column: str,
    adjusted_score_column: str,
) -> pd.DataFrame:
    out = add_age_support_columns(frame, spec)
    age_cfg = spec.get("age_adjustment", {})
    groups = age_cfg.get("groups", {})
    quantiles = age_cfg.get("score_quantiles", {})
    lower = float(quantiles.get("lower", 0.05))
    upper = float(quantiles.get("upper", 0.95))
    enabled = age_adjustment_enabled(spec)

    weighted_components: list[pd.Series] = []
    total_weight = 0.0
    for group_name, group in groups.items():
        rate_column = group.get("rate_column")
        score_column = group.get("score_column")
        weight = float(group.get("within_age_weight", 0.0))
        group_enabled = bool(group.get("enabled", True))

        if score_column not in out.columns:
            out[score_column] = np.nan

        if group_enabled and rate_column in out.columns:
            out[score_column] = robust_score(
                out[rate_column],
                lower_quantile=lower,
                upper_quantile=upper,
                higher_is_worse=True,
            )
            weighted_components.append(out[score_column].fillna(0) * weight)
            total_weight += weight
        else:
            out[score_column] = np.nan

    if enabled and total_weight > 0:
        out["score_age_vulnerability"] = sum(weighted_components) / total_weight
        out["age_adjustment_points"] = (
            out["score_age_vulnerability"].fillna(0) / 100.0 * float(age_cfg.get("max_adjustment_points", 0.0))
        )
    else:
        out["score_age_vulnerability"] = 0.0
        out["age_adjustment_points"] = 0.0

    base_score = pd.to_numeric(out.get(base_score_column), errors="coerce")
    out["age_adjustment_enabled"] = enabled
    out["adjustment_config_version"] = spec.get("config_version")
    out[adjusted_score_column] = (base_score + out["age_adjustment_points"]).clip(0, 100)
    out.loc[base_score.isna(), adjusted_score_column] = np.nan
    return out


def build_adjustment_factor_reference(spec: dict[str, Any]) -> pd.DataFrame:
    age_cfg = spec.get("age_adjustment", {})
    rows = [
        {
            "adjustment_name": age_cfg.get("label", "Age Adjustment"),
            "adjustment_key": "age_adjustment",
            "enabled": age_adjustment_enabled(spec),
            "target_score": age_cfg.get("target_score", "vulnerability_score"),
            "mode": age_cfg.get("mode", "additive_points"),
            "max_adjustment_points": float(age_cfg.get("max_adjustment_points", 0.0)),
            "group_key": "combined",
            "group_label": "Combined age adjustment",
            "within_age_weight": 1.0,
            "acs_variables": "",
            "config_version": spec.get("config_version"),
            "description": age_cfg.get("description", ""),
        }
    ]
    for group_key, group in age_cfg.get("groups", {}).items():
        rows.append(
            {
                "adjustment_name": age_cfg.get("label", "Age Adjustment"),
                "adjustment_key": "age_adjustment",
                "enabled": bool(group.get("enabled", True)),
                "target_score": age_cfg.get("target_score", "vulnerability_score"),
                "mode": age_cfg.get("mode", "additive_points"),
                "max_adjustment_points": float(age_cfg.get("max_adjustment_points", 0.0)),
                "group_key": group_key,
                "group_label": group.get("label", group_key),
                "within_age_weight": float(group.get("within_age_weight", 0.0)),
                "acs_variables": ", ".join(group.get("acs_variables", {}).values()),
                "config_version": spec.get("config_version"),
                "description": age_cfg.get("description", ""),
            }
        )
    return pd.DataFrame(rows)


def build_municipio_adjustment_table(frame: pd.DataFrame, spec: dict[str, Any]) -> pd.DataFrame:
    out = frame.copy()
    if "municipio_slug" not in out.columns:
        if "municipio_key" in out.columns:
            out["municipio_slug"] = out["municipio_key"]
        else:
            out["municipio_slug"] = pd.NA

    adjustment_columns = [
        "municipio",
        "municipio_key",
        "municipio_slug",
        "child_under_5_population",
        "elderly_65_plus_population",
        "child_rate",
        "elderly_65_plus_rate",
        "age_dependency_rate",
        "score_child_vulnerability",
        "score_elderly_vulnerability",
        "score_age_vulnerability",
        "age_adjustment_points",
        "age_adjustment_enabled",
        "vulnerability_score_base",
        "vulnerability_score_adjusted",
        "adjustment_config_version",
    ]
    for column in adjustment_columns:
        if column not in out.columns:
            out[column] = pd.NA
    return out[adjustment_columns].copy()
