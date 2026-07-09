from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.core.config import SQUAD_SAVE_FILE
from app.schemas.fc26 import ChatRequest
from app.services.fc26_agent import answer_scouting_question, generate_scouting_report
from app.services.fc26_loader import data_exists, get_filter_options, load_fc26_players
from app.services.fc26_scoring import PRESETS, rank_players

router = APIRouter(prefix="/api/fc26", tags=["fc26"])


def has_position(position_text, position: str) -> bool:
    selected = position.strip().upper()
    if not selected:
        return True
    positions = [value.strip().upper() for value in str(position_text or "").split(",")]
    return selected in positions


def slot_base_position(slot: str) -> str:
    slot = str(slot or "").strip().upper()
    return {
        "LS": "ST",
        "RS": "ST",
        "LAM": "CAM",
        "RAM": "CAM",
        "LCM": "CM",
        "RCM": "CM",
        "LCDM": "CDM",
        "RCDM": "CDM",
        "LCB": "CB",
        "RCB": "CB",
        "LWB": "LB",
        "RWB": "RB",
    }.get(slot, slot)


def selected_plan_from_payload(payload: dict) -> tuple[str, dict]:
    controls = payload.get("controls") or {}
    plan_key = controls.get("plan") or "base"
    squad_state = payload.get("squadState") or {}
    return plan_key, squad_state.get(plan_key) or squad_state.get("base") or {}


def format_money(value: float) -> str:
    value = float(value or 0)
    if value >= 1_000_000:
        return f"€{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"€{value / 1_000:.0f}K"
    return f"€{value:.0f}"


def player_weakness_reason(item: dict, avg_score: float, avg_overall: float) -> str:
    player = item["player"]
    score = float(item["score"] or 0)
    overall = float(player.get("overall") or 0)
    potential = float(player.get("potential") or 0)
    age = int(float(player.get("age") or 0))
    value = float(player.get("value_eur") or 0)
    wage = float(player.get("wage_eur") or 0)
    growth = potential - overall
    score_gap = score - avg_score
    overall_gap = overall - avg_overall

    reasons = [f"팀 평균 대비 종합점수 {score_gap:+.1f}", f"OVR {overall:.0f}({overall_gap:+.1f})"]
    if growth <= 1:
        reasons.append(f"POT {potential:.0f}로 성장 여지 {growth:+.0f}")
    elif growth >= 5:
        reasons.append(f"POT {potential:.0f}로 성장 여지는 {growth:+.0f}이나 즉시전력 점검 필요")
    else:
        reasons.append(f"POT {potential:.0f}, 성장 여지 {growth:+.0f}")

    if age >= 30:
        reasons.append(f"{age}세라 장기 운용/재판매 리스크")
    elif age <= 23:
        reasons.append(f"{age}세라 경험 리스크")
    else:
        reasons.append(f"{age}세")

    if value >= 80_000_000 or wage >= 200_000:
        reasons.append(f"비용 {format_money(value)} / 주급 {format_money(wage)}")
    elif value > 0 or wage > 0:
        reasons.append(f"비용 {format_money(value)} / 주급 {format_money(wage)}")

    return (
        f"{item['label']}({player.get('short_name')}) 점수 {score:.1f}: "
        f"{', '.join(reasons)} 기준으로 교체/보강 우선 검토"
    )


def summarize_team(payload: dict) -> dict:
    _, plan = selected_plan_from_payload(payload)
    starters = plan.get("starters") or {}
    labels = plan.get("labels") or {}
    selected = []
    for slot, player in starters.items():
        if not player:
            continue
        label = labels.get(slot) or slot
        score = float(player.get("scouting_score") or 0)
        selected.append({"slot": slot, "label": label, "base": slot_base_position(label), "player": player, "score": score})

    if not selected:
        return {
            "summary": "아직 주전 선수가 배치되지 않았습니다.",
            "weaknesses": ["포지션별 전력 평가를 위해 먼저 스쿼드에 선수를 배치해야 합니다."],
            "strengths": [],
            "weak_positions": [],
            "score": 0,
        }

    avg_score = sum(item["score"] for item in selected) / len(selected)
    avg_overall = sum(float(item["player"].get("overall") or 0) for item in selected) / len(selected)
    weak_positions = sorted(selected, key=lambda item: item["score"])[:4]
    strong_positions = sorted(selected, key=lambda item: item["score"], reverse=True)[:3]
    weaknesses = [
        player_weakness_reason(item, avg_score, avg_overall)
        for item in weak_positions
    ]
    strengths = [
        f"{item['label']}({item['player'].get('short_name')}) 점수 {item['score']:.1f}"
        for item in strong_positions
    ]
    return {
        "summary": f"현재 주전 {len(selected)}명의 평균 종합점수는 {avg_score:.1f}, 평균 OVR은 {avg_overall:.1f}입니다.",
        "weaknesses": weaknesses,
        "strengths": strengths,
        "weak_positions": [
            {"slot": item["slot"], "label": item["label"], "base_position": item["base"], "score": item["score"], "player": item["player"]}
            for item in weak_positions
        ],
        "score": avg_score,
    }


def recommend_players(payload: dict, limit: int = 8) -> list[dict]:
    analysis = summarize_team(payload)
    _, plan = selected_plan_from_payload(payload)
    controls = payload.get("controls") or {}
    starters = plan.get("starters") or {}
    assigned_ids = {str(player.get("player_id")) for player in starters.values() if player}
    df = load_fc26_players()
    if df.empty:
        return []

    if controls.get("teamRegion"):
        df = df[df["region"].str.lower().eq(str(controls["teamRegion"]).lower())]
    if controls.get("teamNationality"):
        df = df[df["nationality_name"].str.lower().eq(str(controls["teamNationality"]).lower())]
    if controls.get("teamCandidateLeague"):
        df = df[df["league_name"].str.lower().eq(str(controls["teamCandidateLeague"]).lower())]

    recommendations = []
    target_positions = analysis["weak_positions"] or [{"base_position": "CM", "label": "CM", "score": 0, "player": {}}]
    for target in target_positions:
        position = target["base_position"]
        ranked = rank_players(df, position=position, preset="balanced")
        ranked = ranked[~ranked["player_id"].astype(str).isin(assigned_ids)]
        if ranked.empty:
            continue
        for player in ranked[ranked["player_positions"].apply(lambda value: has_position(value, position))].head(3).to_dict("records"):
            current_score = float(target.get("score") or 0)
            player_score = float(player.get("scouting_score") or 0)
            lift = player_score - current_score
            recommendations.append({
                "player": {key: player.get(key, "") for key in PUBLIC_COLUMNS},
                "target_slot": target.get("slot"),
                "target_position": target.get("label"),
                "current_player": (target.get("player") or {}).get("short_name", "미배치"),
                "score_lift": lift,
                "reasons": [
                    f"잠재력: POT {int(player.get('potential') or 0)}, 성장 여지 {int((player.get('potential') or 0) - (player.get('overall') or 0)):+d}",
                    f"가격: 시장가치 {format_money(player.get('value_eur') or 0)}, 주급 {format_money(player.get('wage_eur') or 0)}",
                    f"공헌도: 종합점수 {player_score:.1f}, 현재 슬롯 대비 {lift:+.1f}",
                    f"내 팀 포지션: {target.get('label')} 보강 후보, 가능 포지션 {player.get('player_positions')}",
                ],
            })
    recommendations.sort(key=lambda item: item["score_lift"], reverse=True)
    return recommendations[:limit]


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


@router.post("/squads")
def save_squad(payload: dict):
    SQUAD_SAVE_FILE.parent.mkdir(parents=True, exist_ok=True)
    saved = {
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "squad": payload,
    }
    SQUAD_SAVE_FILE.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "path": str(SQUAD_SAVE_FILE)}


@router.post("/team-analysis")
def team_analysis(payload: dict):
    return {
        "analysis": summarize_team(payload),
        "recommendations": recommend_players(payload),
    }
