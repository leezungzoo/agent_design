from __future__ import annotations

from functools import lru_cache

import pandas as pd

from app.core.config import FC26_CSV, PLAYER_IMAGE_DIR

RAW_CSV = FC26_CSV

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
    "Afghanistan": "Asia", "Armenia": "Asia", "Azerbaijan": "Asia", "Bangladesh": "Asia",
    "China PR": "Asia", "Chinese Taipei": "Asia", "Georgia": "Asia", "Hong Kong": "Asia",
    "India": "Asia", "Indonesia": "Asia", "Iran": "Asia", "Iraq": "Asia", "Israel": "Asia",
    "Japan": "Asia", "Jordan": "Asia", "Korea Republic": "Asia", "Lebanon": "Asia",
    "Malaysia": "Asia", "Pakistan": "Asia", "Palestine": "Asia", "Philippines": "Asia",
    "Qatar": "Asia", "Saudi Arabia": "Asia", "Sri Lanka": "Asia", "Syria": "Asia",
    "Tajikistan": "Asia", "Thailand": "Asia", "Türkiye": "Asia", "United Arab Emirates": "Asia",
    "Uzbekistan": "Asia", "Yemen": "Asia",
    "Albania": "Europe", "Andorra": "Europe", "Austria": "Europe", "Belarus": "Europe",
    "Belgium": "Europe", "Bosnia and Herzegovina": "Europe", "Bulgaria": "Europe",
    "Croatia": "Europe", "Cyprus": "Europe", "Czechia": "Europe", "Denmark": "Europe",
    "England": "Europe", "Estonia": "Europe", "Faroe Islands": "Europe", "Finland": "Europe",
    "France": "Europe", "Germany": "Europe", "Gibraltar": "Europe", "Greece": "Europe",
    "Hungary": "Europe", "Iceland": "Europe", "Italy": "Europe", "Kosovo": "Europe",
    "Latvia": "Europe", "Liechtenstein": "Europe", "Lithuania": "Europe", "Luxembourg": "Europe",
    "Malta": "Europe", "Moldova": "Europe", "Montenegro": "Europe", "Netherlands": "Europe",
    "North Macedonia": "Europe", "Northern Ireland": "Europe", "Norway": "Europe",
    "Poland": "Europe", "Portugal": "Europe", "Republic of Ireland": "Europe",
    "Romania": "Europe", "Russia": "Europe", "Scotland": "Europe", "Serbia": "Europe",
    "Slovakia": "Europe", "Slovenia": "Europe", "Spain": "Europe", "Sweden": "Europe",
    "Switzerland": "Europe", "Ukraine": "Europe", "Wales": "Europe",
    "Algeria": "Africa", "Angola": "Africa", "Benin": "Africa", "Burkina Faso": "Africa",
    "Burundi": "Africa", "Cabo Verde": "Africa", "Cameroon": "Africa",
    "Central African Republic": "Africa", "Chad": "Africa", "Comoros": "Africa",
    "Congo": "Africa", "Congo DR": "Africa", "Côte d'Ivoire": "Africa", "Egypt": "Africa",
    "Equatorial Guinea": "Africa", "Gabon": "Africa", "Gambia": "Africa", "Ghana": "Africa",
    "Guinea": "Africa", "Guinea-Bissau": "Africa", "Kenya": "Africa", "Liberia": "Africa",
    "Libya": "Africa", "Madagascar": "Africa", "Malawi": "Africa", "Mali": "Africa",
    "Mauritania": "Africa", "Morocco": "Africa", "Mozambique": "Africa", "Namibia": "Africa",
    "Niger": "Africa", "Nigeria": "Africa", "Rwanda": "Africa", "Senegal": "Africa",
    "Sierra Leone": "Africa", "Somalia": "Africa", "South Africa": "Africa",
    "Tanzania": "Africa", "Togo": "Africa", "Tunisia": "Africa", "Uganda": "Africa",
    "Zambia": "Africa", "Zimbabwe": "Africa",
    "Argentina": "South America", "Bolivia": "South America", "Brazil": "South America",
    "Chile": "South America", "Colombia": "South America", "Ecuador": "South America",
    "Guyana": "South America", "Paraguay": "South America", "Peru": "South America",
    "Suriname": "South America", "Uruguay": "South America", "Venezuela": "South America",
    "Antigua and Barbuda": "North America", "Barbados": "North America",
    "Bermuda": "North America", "Canada": "North America", "Costa Rica": "North America",
    "Cuba": "North America", "Curacao": "North America", "Dominican Republic": "North America",
    "El Salvador": "North America", "Grenada": "North America", "Guatemala": "North America",
    "Haiti": "North America", "Honduras": "North America", "Jamaica": "North America",
    "Mexico": "North America", "Montserrat": "North America", "Panama": "North America",
    "Puerto Rico": "North America", "Saint Kitts and Nevis": "North America",
    "Saint Lucia": "North America", "Trinidad and Tobago": "North America",
    "United States": "North America",
    "Australia": "Oceania", "New Caledonia": "Oceania", "New Zealand": "Oceania",
    "Vanuatu": "Oceania",
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
        return f"/static/images/players/{normalized_id}.png"
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
