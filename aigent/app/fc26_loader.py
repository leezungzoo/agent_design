from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT_DIR / "data" / "raw" / "FC26_20250921.csv"
PLAYER_IMAGE_DIR = ROOT_DIR / "app" / "static" / "player_images"

CORE_COLUMNS = [
    "player_id",
    "player_url",
    "short_name",
    "long_name",
    "player_positions",
    "overall",
    "potential",
    "value_eur",
    "wage_eur",
    "age",
    "height_cm",
    "weight_kg",
    "league_name",
    "club_name",
    "club_position",
    "nationality_name",
    "preferred_foot",
    "weak_foot",
    "skill_moves",
    "international_reputation",
    "player_tags",
    "player_traits",
    "pace",
    "shooting",
    "passing",
    "dribbling",
    "defending",
    "physic",
    "attacking_finishing",
    "attacking_short_passing",
    "skill_ball_control",
    "movement_reactions",
    "power_stamina",
    "power_strength",
    "mentality_aggression",
    "mentality_interceptions",
    "mentality_positioning",
    "mentality_vision",
    "mentality_composure",
    "defending_standing_tackle",
    "goalkeeping_diving",
    "goalkeeping_handling",
    "goalkeeping_kicking",
    "goalkeeping_positioning",
    "goalkeeping_reflexes",
    "st",
    "lw",
    "rw",
    "cam",
    "cm",
    "cdm",
    "cb",
    "rb",
    "lb",
    "gk",
    "player_face_url",
]

REGION_MAP = {
    "England": "Europe",
    "Germany": "Europe",
    "Spain": "Europe",
    "France": "Europe",
    "Italy": "Europe",
    "Portugal": "Europe",
    "Netherlands": "Europe",
    "Belgium": "Europe",
    "Croatia": "Europe",
    "Brazil": "South America",
    "Argentina": "South America",
    "Uruguay": "South America",
    "Colombia": "South America",
    "Chile": "South America",
    "Morocco": "Africa",
    "Nigeria": "Africa",
    "Senegal": "Africa",
    "Ghana": "Africa",
    "South Korea": "Asia",
    "Japan": "Asia",
    "Australia": "Asia-Pacific",
    "United States": "North America",
    "Mexico": "North America",
    "Canada": "North America",
}


def data_exists() -> bool:
    return RAW_CSV.exists()


def local_player_image_path(player_id: object) -> str:
    try:
        normalized_id = str(int(float(player_id)))
    except (TypeError, ValueError):
        return ""

    image_path = PLAYER_IMAGE_DIR / f"{normalized_id}.png"
    if image_path.exists():
        return f"/static/player_images/{normalized_id}.png"
    return ""


@lru_cache(maxsize=1)
def load_fc26_players() -> pd.DataFrame:
    if not RAW_CSV.exists():
        return pd.DataFrame(columns=CORE_COLUMNS + ["region"])

    df = pd.read_csv(RAW_CSV, low_memory=False)
    for column in CORE_COLUMNS:
        if column not in df.columns:
            df[column] = None

    df = df[CORE_COLUMNS].copy()
    numeric_columns = [
        "overall",
        "potential",
        "value_eur",
        "wage_eur",
        "age",
        "height_cm",
        "weight_kg",
        "weak_foot",
        "skill_moves",
        "international_reputation",
        "pace",
        "shooting",
        "passing",
        "dribbling",
        "defending",
        "physic",
        "attacking_finishing",
        "attacking_short_passing",
        "skill_ball_control",
        "movement_reactions",
        "power_stamina",
        "power_strength",
        "mentality_aggression",
        "mentality_interceptions",
        "mentality_positioning",
        "mentality_vision",
        "mentality_composure",
        "defending_standing_tackle",
        "goalkeeping_diving",
        "goalkeeping_handling",
        "goalkeeping_kicking",
        "goalkeeping_positioning",
        "goalkeeping_reflexes",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    text_columns = [
        "short_name",
        "long_name",
        "player_positions",
        "league_name",
        "club_name",
        "club_position",
        "nationality_name",
        "preferred_foot",
        "player_tags",
        "player_traits",
        "player_face_url",
    ]
    for column in text_columns:
        df[column] = df[column].fillna("").astype(str)

    df["region"] = df["nationality_name"].map(REGION_MAP).fillna("Other")
    df["player_image_path"] = df["player_id"].apply(local_player_image_path)
    return df


def get_filter_options() -> dict:
    df = load_fc26_players()
    if df.empty:
        return {"positions": [], "nationalities": [], "regions": [], "leagues": [], "clubs": []}

    positions = sorted({position.strip() for values in df["player_positions"] for position in values.split(",") if position.strip()})
    league_clubs = {}
    for league, group in df[df["league_name"].astype(bool)].groupby("league_name"):
        league_clubs[league] = sorted(value for value in group["club_name"].dropna().unique().tolist() if value)

    return {
        "positions": positions,
        "nationalities": sorted(df["nationality_name"].dropna().unique().tolist()),
        "regions": sorted(df["region"].dropna().unique().tolist()),
        "leagues": sorted(value for value in df["league_name"].dropna().unique().tolist() if value),
        "clubs": sorted(value for value in df["club_name"].dropna().unique().tolist() if value),
        "league_clubs": league_clubs,
    }
