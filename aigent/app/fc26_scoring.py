from __future__ import annotations

import math

import pandas as pd

PRESETS = {
    "balanced": {"ability": 0.35, "potential": 0.25, "value": 0.15, "fit": 0.15, "geo": 0.10},
    "ready_now": {"ability": 0.50, "potential": 0.10, "value": 0.15, "fit": 0.20, "geo": 0.05},
    "prospect": {"ability": 0.20, "potential": 0.45, "value": 0.15, "fit": 0.15, "geo": 0.05},
    "value": {"ability": 0.25, "potential": 0.15, "value": 0.40, "fit": 0.15, "geo": 0.05},
    "geo": {"ability": 0.25, "potential": 0.20, "value": 0.15, "fit": 0.15, "geo": 0.25},
}

POSITION_RATING_COLUMNS = {
    "ST": "st",
    "LW": "lw",
    "RW": "rw",
    "CAM": "cam",
    "CM": "cm",
    "CDM": "cdm",
    "CB": "cb",
    "RB": "rb",
    "LB": "lb",
    "GK": "gk",
}


def normalize(series: pd.Series, inverse: bool = False) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce").fillna(0)
    low = numeric.min()
    high = numeric.max()
    if high == low:
        values = pd.Series([0.5] * len(numeric), index=numeric.index)
    else:
        values = (numeric - low) / (high - low)
    return 1 - values if inverse else values


def parse_position_rating(value: object) -> float:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return 0
    text = str(value).strip()
    if not text:
        return 0
    base = text.split("+", 1)[0].split("-", 1)[0]
    return float(base) if base.isdigit() else 0


def infer_role(position: str) -> str:
    position = position.upper()
    if position == "GK":
        return "goalkeeper"
    if position in {"CB", "RB", "LB", "RWB", "LWB"}:
        return "defender"
    if position in {"CM", "CDM", "CAM", "LM", "RM"}:
        return "midfielder"
    return "attacker"


def ability_score(df: pd.DataFrame, position: str = "") -> pd.Series:
    role = infer_role(position or "CM")
    if role == "goalkeeper":
        cols = {
            "goalkeeping_diving": 0.20,
            "goalkeeping_handling": 0.20,
            "goalkeeping_positioning": 0.20,
            "goalkeeping_reflexes": 0.25,
            "goalkeeping_kicking": 0.15,
        }
    elif role == "defender":
        cols = {
            "defending": 0.35,
            "physic": 0.20,
            "mentality_interceptions": 0.20,
            "defending_standing_tackle": 0.15,
            "power_strength": 0.10,
        }
    elif role == "attacker":
        cols = {
            "shooting": 0.30,
            "pace": 0.20,
            "dribbling": 0.20,
            "physic": 0.10,
            "attacking_finishing": 0.20,
        }
    else:
        cols = {
            "passing": 0.30,
            "dribbling": 0.20,
            "mentality_vision": 0.20,
            "attacking_short_passing": 0.15,
            "movement_reactions": 0.15,
        }

    score = pd.Series(0.0, index=df.index)
    for column, weight in cols.items():
        score += normalize(df[column]) * weight
    return score


def fit_score(df: pd.DataFrame, position: str = "") -> pd.Series:
    if not position:
        return normalize(df["overall"])

    position = position.upper()
    rating_column = POSITION_RATING_COLUMNS.get(position)
    rating = df[rating_column].map(parse_position_rating) if rating_column in df.columns else df["overall"]
    primary = df["player_positions"].str.split(",").str[0].str.strip().str.upper().eq(position).astype(float)
    any_match = df["player_positions"].str.upper().str.contains(position, regex=False).astype(float)
    return normalize(rating) * 0.60 + primary * 0.25 + any_match * 0.15


def geo_score(df: pd.DataFrame, country: str = "", region: str = "", league: str = "") -> pd.Series:
    score = pd.Series(0.3, index=df.index)
    if country:
        score += df["nationality_name"].str.lower().eq(country.lower()).astype(float) * 0.4
    if region:
        score += df["region"].str.lower().eq(region.lower()).astype(float) * 0.3
    if league:
        score += df["league_name"].str.lower().eq(league.lower()).astype(float) * 0.2
    return score.clip(upper=1.0)


def rank_players(
    df: pd.DataFrame,
    position: str = "",
    preset: str = "balanced",
    country: str = "",
    region: str = "",
    league: str = "",
) -> pd.DataFrame:
    if df.empty:
        result = df.copy()
        for column in ["ability_score", "potential_score", "value_score", "fit_score", "geo_score", "scouting_score"]:
            result[column] = pd.Series(dtype=float)
        return result

    weights = PRESETS.get(preset, PRESETS["balanced"])
    result = df.copy()
    result["ability_score"] = ability_score(result, position)
    result["potential_score"] = normalize(result["potential"]) * 0.70 + normalize(result["potential"] - result["overall"]) * 0.30
    value_efficiency = result["overall"] / result["value_eur"].apply(lambda v: math.log(float(v) + 1) + 1)
    wage_efficiency = result["overall"] / result["wage_eur"].apply(lambda v: math.log(float(v) + 1) + 1)
    result["value_score"] = normalize(value_efficiency) * 0.6 + normalize(wage_efficiency) * 0.4
    result["fit_score"] = fit_score(result, position)
    result["geo_score"] = geo_score(result, country=country, region=region, league=league)
    result["scouting_score"] = (
        result["ability_score"] * weights["ability"]
        + result["potential_score"] * weights["potential"]
        + result["value_score"] * weights["value"]
        + result["fit_score"] * weights["fit"]
        + result["geo_score"] * weights["geo"]
    ) * 100
    return result.sort_values("scouting_score", ascending=False)
