from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query

from app.fc26_agent import answer_scouting_question, generate_scouting_report
from app.fc26_loader import data_exists, get_filter_options, load_fc26_players
from app.fc26_scoring import PRESETS, rank_players

router = APIRouter(prefix="/api/fc26", tags=["fc26"])


class ChatRequest(BaseModel):
    question: str


def has_position(position_text, position: str) -> bool:
    selected = position.strip().upper()
    if not selected:
        return True
    positions = [value.strip().upper() for value in str(position_text or "").split(",")]
    return selected in positions


PUBLIC_COLUMNS = [
    "player_id",
    "short_name",
    "long_name",
    "player_positions",
    "overall",
    "potential",
    "value_eur",
    "wage_eur",
    "age",
    "league_name",
    "club_name",
    "club_position",
    "nationality_name",
    "region",
    "preferred_foot",
    "player_tags",
    "player_traits",
    "pace",
    "shooting",
    "passing",
    "dribbling",
    "defending",
    "physic",
    "player_image_path",
    "player_face_url",
    "ability_score",
    "potential_score",
    "value_score",
    "fit_score",
    "geo_score",
    "scouting_score",
]


@router.get("/meta")
def meta():
    df = load_fc26_players()
    return {
        "data_loaded": data_exists(),
        "count": int(len(df)),
        "presets": list(PRESETS.keys()),
        "filters": get_filter_options(),
    }


@router.get("/players")
def players(
    search: str = "",
    position: str = "",
    nationality: str = "",
    region: str = "",
    league: str = "",
    club: str = "",
    preset: str = "balanced",
    max_age: int | None = Query(default=None, ge=15, le=60),
    max_value: int | None = Query(default=None, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
):
    df = load_fc26_players()
    if df.empty:
        return {"count": 0, "players": [], "message": "FC26 CSV not found in data/raw/FC26_20250921.csv"}

    filtered = df.copy()
    if search:
        needle = search.lower()
        filtered = filtered[
            filtered["short_name"].str.lower().str.contains(needle, regex=False)
            | filtered["long_name"].str.lower().str.contains(needle, regex=False)
        ]
    if position:
        filtered = filtered[filtered["player_positions"].apply(lambda value: has_position(value, position))]
    if nationality:
        filtered = filtered[filtered["nationality_name"].str.lower().eq(nationality.lower())]
    if region:
        filtered = filtered[filtered["region"].str.lower().eq(region.lower())]
    if league:
        filtered = filtered[filtered["league_name"].str.lower().eq(league.lower())]
    if club:
        filtered = filtered[filtered["club_name"].str.lower().eq(club.lower())]
    if max_age is not None:
        filtered = filtered[filtered["age"] <= max_age]
    if max_value is not None:
        filtered = filtered[filtered["value_eur"] <= max_value]

    ranked = rank_players(filtered, position=position, preset=preset, country=nationality, region=region, league=league)
    rows = ranked[PUBLIC_COLUMNS].head(limit).fillna("").to_dict("records")
    return {"count": int(len(filtered)), "players": rows}


@router.get("/report/{player_id}")
def report(
    player_id: int,
    position: str = "",
    nationality: str = "",
    region: str = "",
    league: str = "",
    preset: str = "balanced",
):
    df = load_fc26_players()
    if df[df["player_id"] == player_id].empty:
        raise HTTPException(status_code=404, detail="Player not found")

    ranked = rank_players(df, position=position, preset=preset, country=nationality, region=region, league=league)
    selected = ranked[ranked["player_id"] == player_id]
    player = selected.iloc[0].fillna("").to_dict()
    report_text, report_source = generate_scouting_report(player)
    return {"player": player, "report": report_text, "report_source": report_source}


@router.post("/chat/{player_id}")
def chat(
    player_id: int,
    request: ChatRequest,
    position: str = "",
    nationality: str = "",
    region: str = "",
    league: str = "",
    preset: str = "balanced",
):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    df = load_fc26_players()
    if df[df["player_id"] == player_id].empty:
        raise HTTPException(status_code=404, detail="Player not found")

    ranked = rank_players(df, position=position, preset=preset, country=nationality, region=region, league=league)
    selected = ranked[ranked["player_id"] == player_id]
    player = selected.iloc[0].fillna("").to_dict()
    answer, source = answer_scouting_question(player, question)
    return {"player": player, "question": question, "answer": answer, "source": source}
