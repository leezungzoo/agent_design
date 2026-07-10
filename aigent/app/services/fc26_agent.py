from __future__ import annotations

import json
import os
from urllib.parse import quote

import requests

from app.core.config import ENV_PATH, SQUAD_SAVE_FILE
from app.services.fc26_middleware import (
    get_session,
    human_in_the_loop_middleware,
    middleware_state,
    model_call_limit_middleware,
    summarization_middleware,
    tool_call_limit_middleware,
)

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False


load_dotenv(ENV_PATH)


def grade(score: float) -> str:
    if score >= 85:
        return "S"
    if score >= 75:
        return "A"
    if score >= 65:
        return "B"
    if score >= 55:
        return "C"
    return "D"


def money(value: float) -> str:
    if value >= 1_000_000:
        return f"€{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"€{value / 1_000:.0f}K"
    return f"€{value:.0f}"


def wikipedia_headers() -> dict:
    return {
        "User-Agent": "FC26ScoutingAgent/1.0 (local scouting research app)",
        "Accept": "application/json",
    }


def wikipedia_search_title(query: str, language: str = "en") -> str:
    if not query.strip():
        return ""
    response = requests.get(
        f"https://{language}.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": 1,
        },
        headers=wikipedia_headers(),
        timeout=8,
    )
    response.raise_for_status()
    results = response.json().get("query", {}).get("search", [])
    return results[0].get("title", "") if results else ""


def wikipedia_summary(title: str, language: str = "en") -> dict:
    if not title.strip():
        return {}
    response = requests.get(
        f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{quote(title, safe='')}",
        headers=wikipedia_headers(),
        timeout=8,
    )
    response.raise_for_status()
    data = response.json()
    return {
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "extract": data.get("extract", ""),
        "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        "source": "Wikipedia",
        "language": language,
    }


def wikipedia_full_extract(title: str, language: str = "en") -> str:
    if not title.strip():
        return ""
    response = requests.get(
        f"https://{language}.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "prop": "extracts",
            "titles": title,
            "explaintext": 1,
            "exsectionformat": "plain",
            "format": "json",
            "redirects": 1,
        },
        headers=wikipedia_headers(),
        timeout=8,
    )
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})
    for page in pages.values():
        extract = page.get("extract", "")
        if extract:
            return extract
    return ""


def fetch_wikipedia_context(player: dict) -> dict:
    long_name = player.get("long_name") or ""
    short_name = player.get("short_name") or ""
    nationality = player.get("nationality_name") or ""
    club = player.get("club_name") or ""

    queries = []
    for query in [
        f"{long_name} footballer {nationality}",
        f"{short_name} footballer {nationality}",
        f"{short_name} {club} footballer",
        f"{short_name} footballer",
        long_name,
        short_name,
    ]:
        query = query.strip()
        if query and query not in queries:
            queries.append(query)

    for language in ("en", "ko"):
        for query in queries:
            try:
                title = wikipedia_search_title(query, language=language)
                if title:
                    summary = wikipedia_summary(title, language=language)
                    if summary.get("extract"):
                        summary["full_extract"] = wikipedia_full_extract(title, language=language)
                        return summary
            except Exception:
                continue
    return {}


def format_wikipedia_context(context: dict) -> str:
    if not context:
        return "Wikipedia 공개 정보: 찾지 못함"
    return (
        f"Wikipedia 공개 정보({context.get('language', 'en')}):\n"
        f"- 제목: {context.get('title')}\n"
        f"- 설명: {context.get('description')}\n"
        f"- 요약: {context.get('extract')}\n"
        f"- URL: {context.get('url')}"
    )


def generate_template_scouting_report(player: dict) -> str:
    score = float(player.get("scouting_score", 0))
    strengths = sorted(
        [
            ("pace", player.get("pace", 0)),
            ("shooting", player.get("shooting", 0)),
            ("passing", player.get("passing", 0)),
            ("dribbling", player.get("dribbling", 0)),
            ("defending", player.get("defending", 0)),
            ("physic", player.get("physic", 0)),
        ],
        key=lambda item: item[1] or 0,
        reverse=True,
    )[:3]
    strength_text = ", ".join(f"{name} {int(value)}" for name, value in strengths if value)

    value = float(player.get("value_eur", 0) or 0)
    wage = float(player.get("wage_eur", 0) or 0)
    age = int(player.get("age", 0) or 0)
    growth = float(player.get("potential", 0) or 0) - float(player.get("overall", 0) or 0)

    if growth >= 8 and age <= 23:
        upside = "성장 여지가 큰 유망주형 타깃입니다."
    elif score >= 75:
        upside = "즉시전력으로 활용 가능한 상위권 후보입니다."
    else:
        upside = "특정 전술/예산 조건에 맞춰 검토할 후보입니다."

    risk = []
    if value >= 80_000_000:
        risk.append("이적료 부담이 큽니다")
    if wage >= 200_000:
        risk.append("주급 부담이 큽니다")
    if age >= 31:
        risk.append("장기 성장성은 제한적입니다")
    if not risk:
        risk.append("뚜렷한 재정 리스크는 낮은 편입니다")

    return (
        f"{player.get('short_name')} 스카우팅 리포트\n\n"
        f"- 등급: {grade(score)} / 종합 점수: {score:.1f}\n"
        f"- 포지션: {player.get('player_positions')} / 클럽: {player.get('club_name') or '-'}\n"
        f"- 국적/지역: {player.get('nationality_name')} / {player.get('region')}\n"
        f"- 나이: {age}, OVR/POT: {int(player.get('overall', 0))}/{int(player.get('potential', 0))}\n"
        f"- 시장가치/주급: {money(value)} / {money(wage)}\n\n"
        f"요약: {upside}\n\n"
        f"강점: {strength_text or '주요 능력치 확인 필요'}.\n"
        f"리스크: {', '.join(risk)}.\n\n"
        "지역/적응 판단: 현재 데이터에는 고향/거주지 컬럼이 없으므로 국적, 소속 리그, 클럽을 proxy로 사용합니다. "
        "국적과 타깃 리그/지역 조건이 가까울수록 적응 리스크를 낮게 평가합니다."
    )


def get_openai_api_key() -> str:
    return (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("open_api_key")
        or os.getenv("OPEN_API_KEY")
        or os.getenv("openai_api_key")
        or ""
    ).strip()


def compact_player_context(player: dict) -> dict:
    keys = [
        "short_name",
        "long_name",
        "player_positions",
        "club_name",
        "league_name",
        "nationality_name",
        "region",
        "age",
        "overall",
        "potential",
        "value_eur",
        "wage_eur",
        "preferred_foot",
        "weak_foot",
        "skill_moves",
        "international_reputation",
        "pace",
        "shooting",
        "passing",
        "dribbling",
        "defending",
        "physic",
        "player_tags",
        "player_traits",
        "ability_score",
        "potential_score",
        "value_score",
        "fit_score",
        "geo_score",
        "scouting_score",
    ]
    return {key: player.get(key, "") for key in keys}


def is_greeting_question(question: str) -> bool:
    normalized = (
        question.lower()
        .strip()
        .strip(" \t\r\n.,!?~ㅋㅎㅠㅜ;:()[]{}'\"`")
    )
    greeting_words = {
        "안녕",
        "안녕하세요",
        "안녕하세여",
        "안녕하십니까",
        "하이",
        "헬로",
        "hello",
        "hi",
        "hey",
    }
    return normalized in greeting_words


def greeting_answer() -> str:
    return "안녕하세요, 저는 당신의 비서 fc agent입니다!"


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


POSITION_ROLE_GUIDES = {
    "GK": "최후방 빌드업 시작점이자 박스 보호자입니다. 선방, 크로스 처리, 뒷공간 커버 안정성이 핵심입니다.",
    "CB": "수비 라인의 기준점입니다. 제공권, 1대1 수비, 라인 컨트롤, 전진 패스 판단을 맡습니다.",
    "LB": "왼쪽 측면의 폭과 수비 밸런스를 담당합니다. 오버래핑, 크로스, 뒷공간 관리가 중요합니다.",
    "RB": "오른쪽 측면의 전진 통로와 전환 수비를 맡습니다. 활동량, 크로스, 측면 압박 대응이 핵심입니다.",
    "CDM": "수비 앞 1차 보호막입니다. 인터셉트, 세컨볼 회수, 후방 빌드업 연결, 역습 차단을 맡습니다.",
    "CM": "공수 연결축입니다. 압박 회피, 전진 패스, 박스 투 박스 활동량, 템포 조절이 중요합니다.",
    "CAM": "공격 전개의 창의성 담당입니다. 최종 패스, 하프스페이스 점유, 슈팅 찬스 생성이 핵심입니다.",
    "LM": "왼쪽 측면 전개와 수비 가담을 함께 맡는 밸런스형 측면 자원입니다.",
    "RM": "오른쪽 측면 전개와 수비 가담을 함께 맡는 밸런스형 측면 자원입니다.",
    "LW": "왼쪽 공격 폭과 1대1 돌파를 담당합니다. 안쪽 침투, 컷인, 크로스, 압박 시작점 역할이 중요합니다.",
    "RW": "오른쪽 공격 폭과 1대1 돌파를 담당합니다. 컷인, 뒷공간 침투, 크로스, 전방 압박을 맡습니다.",
    "ST": "최전방 득점 기준점입니다. 침투, 마무리, 압박 유도, 포스트 플레이 또는 라인 브레이킹이 핵심입니다.",
}


def load_saved_squad() -> dict:
    try:
        if not SQUAD_SAVE_FILE.exists():
            return {}
        return json.loads(SQUAD_SAVE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def selected_squad_plan(saved: dict) -> tuple[dict, dict]:
    squad = saved.get("squad") or {}
    controls = squad.get("controls") or {}
    squad_state = squad.get("squadState") or {}
    plan_key = controls.get("plan") or "base"
    return controls, squad_state.get(plan_key) or squad_state.get("base") or {}


def strengths_for_role(player: dict, base_position: str) -> list[str]:
    values = [
        ("스피드", player.get("pace", 0)),
        ("슈팅", player.get("shooting", 0)),
        ("패싱", player.get("passing", 0)),
        ("드리블", player.get("dribbling", 0)),
        ("수비", player.get("defending", 0)),
        ("피지컬", player.get("physic", 0)),
    ]
    if base_position == "GK":
        return ["골키퍼 전용 세부 수치는 현재 공개 컬럼에 제한적이므로 OVR/POT와 traits 중심으로 판단"]
    ranked = sorted(values, key=lambda item: float(item[1] or 0), reverse=True)
    return [f"{name} {int(value)}" for name, value in ranked[:3] if value]


def is_saved_squad_role_question(question: str) -> bool:
    question_lower = question.lower()
    squad_keywords = ["저장", "스쿼드", "squad", "json", "브리핑", "전술 브리핑"]
    role_keywords = ["역할", "브리핑", "포지션", "role", "임무", "맡아", "뭘 해야"]
    return any(keyword in question_lower for keyword in squad_keywords) and any(
        keyword in question_lower for keyword in role_keywords
    )


def is_saved_squad_fit_question(question: str) -> bool:
    question_lower = question.lower()
    squad_keywords = ["저장", "스쿼드", "squad", "json"]
    fit_keywords = [
        "어디",
        "어느",
        "쓸 수",
        "써야",
        "기용",
        "배치",
        "넣",
        "사용",
        "활용",
        "맞는 자리",
        "자리",
        "slot",
        "fit",
    ]
    return any(keyword in question_lower for keyword in squad_keywords) and any(
        keyword in question_lower for keyword in fit_keywords
    )


def player_position_set(player: dict) -> set[str]:
    return {
        value.strip().upper()
        for value in str(player.get("player_positions") or "").split(",")
        if value.strip()
    }


def saved_squad_fit_brief(player: dict) -> str | None:
    saved = load_saved_squad()
    if not saved:
        return None

    controls, plan = selected_squad_plan(saved)
    starters = plan.get("starters") or {}
    labels = plan.get("labels") or {}
    if not starters:
        return None

    positions = player_position_set(player)
    player_score = float(player.get("scouting_score") or 0)
    player_fit = float(player.get("fit_score") or 0) * 100
    assigned_slot = None
    candidates = []

    for slot, starter in starters.items():
        label = labels.get(slot) or slot
        base = slot_base_position(label)
        current_score = float((starter or {}).get("scouting_score") or 0)
        compatible = base in positions or slot_base_position(slot) in positions or slot.upper() in positions
        same_player = starter and str(starter.get("player_id") or "") == str(player.get("player_id") or "")

        if same_player:
            assigned_slot = slot
        if compatible or same_player:
            candidates.append({
                "slot": slot,
                "label": label,
                "base": base,
                "current": starter or {},
                "current_score": current_score,
                "lift": player_score - current_score,
                "same_player": same_player,
            })

    if not candidates:
        slots_text = ", ".join(starters.keys())
        return (
            f"저장된 스쿼드 기준으로 {player.get('short_name')}의 가능 포지션({player.get('player_positions')})과 "
            f"현재 포메이션 슬롯({slots_text})이 직접 맞는 곳은 없습니다.\n\n"
            "후보로 쓰려면 포메이션을 바꾸거나, 선수의 보조 포지션/역할 적응을 별도로 확인해야 합니다."
        )

    candidates.sort(key=lambda item: (item["same_player"], item["lift"], item["current_score"]), reverse=True)
    primary = candidates[0]
    formation = controls.get("formation") or "-"
    team = controls.get("teamClub") or controls.get("teamLeague") or "저장 스쿼드"

    lines = []
    for item in candidates[:4]:
        current = item["current"]
        if item["same_player"]:
            reason = "현재 이미 배치된 슬롯"
        elif item["lift"] >= 8:
            reason = f"현재 선수 대비 큰 업그레이드({item['lift']:+.1f})"
        elif item["lift"] >= 0:
            reason = f"현재 선수 대비 소폭 우위({item['lift']:+.1f})"
        else:
            reason = f"현재 선수 대비 점수는 낮음({item['lift']:+.1f})"
        lines.append(
            f"- {item['slot']}({item['label']}): 현재 {current.get('short_name') or '미배치'}, {reason}"
        )

    base = primary["base"]
    role = POSITION_ROLE_GUIDES.get(base, "이 슬롯의 역할은 팀 전술과 주변 배치에 맞춰 해석해야 합니다.")
    strengths = ", ".join(strengths_for_role(player, base)) or "주요 능력치 확인 필요"
    assigned_note = f" 현재 저장 스쿼드에서는 {assigned_slot}에 이미 배치되어 있습니다." if assigned_slot else ""

    return (
        f"저장된 스쿼드 기준으로 {player.get('short_name')}은 {primary['slot']}({primary['label']})에 쓰는 것이 가장 자연스럽습니다.{assigned_note}\n\n"
        f"- 팀/포메이션: {team} / {formation}\n"
        f"- 선수 가능 포지션: {player.get('player_positions')}\n"
        f"- 추천 1순위 역할: {role}\n"
        f"- 근거 능력치: {strengths}\n"
        f"- 현재 Fit/스카우팅 점수: {player_fit:.0f}점 / {player_score:.1f}\n\n"
        "저장 스쿼드 내 후보 슬롯:\n"
        f"{chr(10).join(lines)}"
    )


def saved_squad_role_brief(player: dict, question: str) -> str | None:
    question_upper = question.upper()
    saved = load_saved_squad()
    if not saved:
        return None

    controls, plan = selected_squad_plan(saved)
    starters = plan.get("starters") or {}
    labels = plan.get("labels") or {}
    if not starters:
        return None

    requested_slots = [
        slot
        for slot in starters
        if slot.upper() in question_upper or (labels.get(slot) or "").upper() in question_upper
    ]
    selected_slot = None
    if requested_slots:
        selected_slot = requested_slots[0]
    else:
        player_id = str(player.get("player_id") or "")
        for slot, starter in starters.items():
            if starter and str(starter.get("player_id") or "") == player_id:
                selected_slot = slot
                break

    if not selected_slot:
        return (
            f"저장된 스쿼드 기준으로 {player.get('short_name')}은 현재 주전 슬롯에 배치되어 있지 않습니다.\n\n"
            "스쿼드에 배치한 뒤 '이 선수의 저장 스쿼드 역할 브리핑해줘' 또는 'LW 역할 브리핑해줘'처럼 물어보면 됩니다."
        )

    starter = starters.get(selected_slot) or {}
    label = labels.get(selected_slot) or selected_slot
    base = slot_base_position(label)
    role = POSITION_ROLE_GUIDES.get(base, "해당 슬롯의 전술 역할은 팀 전술과 주변 배치에 맞춰 해석해야 합니다.")
    traits = starter.get("player_traits") or "특이 traits 없음"
    tags = starter.get("player_tags") or "태그 없음"
    strengths = ", ".join(strengths_for_role(starter, base)) or "주요 능력치 확인 필요"
    formation = controls.get("formation") or "-"
    team = controls.get("teamClub") or controls.get("teamLeague") or "저장 스쿼드"
    fit_score = float(starter.get("fit_score") or 0) * 100
    scouting_score = float(starter.get("scouting_score") or 0)

    return (
        f"저장된 스쿼드 기준 역할 브리핑입니다.\n\n"
        f"- 팀/포메이션: {team} / {formation}\n"
        f"- 슬롯: {selected_slot} ({label})\n"
        f"- 배치 선수: {starter.get('short_name') or '-'} / 가능 포지션 {starter.get('player_positions') or '-'}\n"
        f"- 역할 요약: {role}\n\n"
        f"이 선수에게 기대할 역할:\n"
        f"{starter.get('short_name')}은 이 슬롯에서 {strengths}를 바탕으로 역할을 수행하는 자원입니다. "
        f"현재 Fit은 {fit_score:.0f}점, 스카우팅 점수는 {scouting_score:.1f}입니다.\n\n"
        f"운용 포인트:\n"
        f"- traits: {traits}\n"
        f"- tags: {tags}\n"
        f"- 주변 선수와의 연결을 볼 때, 이 슬롯은 기본 역할뿐 아니라 팀의 약한 구간을 보완하는 방식으로 써야 합니다."
    )


def generate_openai_scouting_report(player: dict) -> str:
    api_key = get_openai_api_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": (
                    "너는 유럽 축구 클럽의 전문 스카우팅 디렉터다. "
                    "FC26 데이터 기반이라는 한계를 명확히 인식하고, 제공된 수치만 근거로 한국어 리포트를 작성한다. "
                    "고향/사는 곳 직접 컬럼은 없으므로 nationality_name, league_name, club_name, region을 지역 적응 proxy로 해석한다. "
                    "과장하지 말고 영입 의사결정에 바로 쓸 수 있게 간결하고 구체적으로 작성한다."
                ),
            },
            {
                "role": "user",
                "content": (
                    "아래 선수 데이터를 기반으로 스카우팅 리포트를 작성해줘.\n"
                    "형식:\n"
                    "1. 한 줄 결론\n"
                    "2. 선수 요약\n"
                    "3. 강점\n"
                    "4. 약점/리스크\n"
                    "5. 전술 적합도\n"
                    "6. 지역/적응 요소\n"
                    "7. 추천 등급\n\n"
                    f"선수 데이터: {compact_player_context(player)}"
                ),
            },
        ],
        "max_output_tokens": 850,
    }
    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=25,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("output_text"):
        return data["output_text"].strip()

    chunks = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(content["text"])
    if not chunks:
        raise RuntimeError("OpenAI response did not include text")
    return "\n".join(chunks).strip()


def generate_scouting_report(player: dict) -> tuple[str, str]:
    try:
        return generate_openai_scouting_report(player), "openai"
    except Exception:
        return generate_template_scouting_report(player), "template_fallback"


def generate_template_chat_answer(player: dict, question: str) -> str:
    question_lower = question.lower()
    value = float(player.get("value_eur", 0) or 0)
    wage = float(player.get("wage_eur", 0) or 0)
    age = int(player.get("age", 0) or 0)
    overall = float(player.get("overall", 0) or 0)
    potential = float(player.get("potential", 0) or 0)
    growth = potential - overall
    strengths = sorted(
        [
            ("스피드", player.get("pace", 0)),
            ("슈팅", player.get("shooting", 0)),
            ("패싱", player.get("passing", 0)),
            ("드리블", player.get("dribbling", 0)),
            ("수비", player.get("defending", 0)),
            ("피지컬", player.get("physic", 0)),
        ],
        key=lambda item: item[1] or 0,
        reverse=True,
    )[:3]
    strength_text = ", ".join(f"{name} {int(score)}" for name, score in strengths if score)
    weakest = sorted(
        [
            ("스피드", player.get("pace", 0)),
            ("슈팅", player.get("shooting", 0)),
            ("패싱", player.get("passing", 0)),
            ("드리블", player.get("dribbling", 0)),
            ("수비", player.get("defending", 0)),
            ("피지컬", player.get("physic", 0)),
        ],
        key=lambda item: item[1] or 0,
    )[:2]
    weakness_text = ", ".join(f"{name} {int(score)}" for name, score in weakest if score)
    score = float(player.get("scouting_score", 0) or 0)
    fit_score = float(player.get("fit_score", 0) or 0) * 100
    value_score = float(player.get("value_score", 0) or 0) * 100

    if is_greeting_question(question):
        return greeting_answer()

    def public_note() -> str:
        context = fetch_wikipedia_context(player)
        if not context.get("extract"):
            return ""
        return (
            f"\n\n공개 이력 참고: {context.get('extract')[:450]}"
            f"\n근거: {context.get('url')}"
        )

    def public_profile_answer() -> str:
        context = fetch_wikipedia_context(player)
        if not context.get("extract"):
            return (
                f"{player.get('short_name')}에 대한 Wikipedia 공개 정보를 찾지 못했습니다.\n\n"
                f"현재 CSV 기준으로는 국적 {player.get('nationality_name')}, 지역 {player.get('region')}, "
                f"소속 리그 {player.get('league_name') or '-'}, 클럽 {player.get('club_name') or '-'}만 확인됩니다."
            )
        full_extract = (context.get("full_extract") or context.get("extract") or "").strip()
        detail_limit = 2200 if any(keyword in question_lower for keyword in ["자세", "상세", "더", "많이", "전체", "full", "detail"]) else 1400
        detail = full_extract[:detail_limit].strip()
        if len(full_extract) > detail_limit:
            detail = f"{detail}\n\n... (더 긴 원문은 근거 링크에서 확인 가능)"
        return (
            f"{player.get('short_name')}의 Wikipedia 공개 정보입니다.\n\n"
            f"- 제목: {context.get('title') or '-'}\n"
            f"- 설명: {context.get('description') or '-'}\n"
            f"- 요약: {context.get('extract')}\n\n"
            f"상세 공개 정보:\n{detail}\n\n"
            f"- 근거: {context.get('url')}"
        )

    wikipedia_keywords = [
        "위키",
        "위키피디아",
        "wikipedia",
        "공개 정보",
        "공개 이력",
        "프로필",
        "profile",
        "근거",
        "출처",
        "source",
    ]
    wikipedia_question = any(keyword in question_lower for keyword in wikipedia_keywords)

    location_keywords = [
        "지역",
        "적응",
        "고향",
        "사는",
        "살아",
        "살고",
        "거주",
        "거주지",
        "집",
        "주소",
        "출생",
        "출생지",
        "태어난",
        "태어났",
        "출신",
        "국가",
        "국적",
        "리그",
        "문화",
        "언어",
        "where live",
        "where does",
        "hometown",
        "birthplace",
        "birth place",
        "residence",
        "address",
    ]
    location_question = any(keyword in question_lower for keyword in location_keywords)

    tactic_keywords = ["전술", "역할", "포지션", "fit", "role", "tactic", "활용", "배치", "기용", "어느 자리"]
    tactic_question = any(keyword in question_lower for keyword in tactic_keywords)

    def has_any(keywords: list[str]) -> bool:
        return any(keyword in question_lower for keyword in keywords)

    def local_mini_scouting_answer() -> str:
        intents = []
        if has_any(["영입", "데려", "사야", "계약", "보강", "추천", "어때", "필요", "주전", "후보"]):
            intents.append("recruit")
        if has_any(["어떻게", "활용", "기용", "배치", "역할", "전술", "포지션", "자리", "써야", "쓸까", "운용"]):
            intents.append("usage")
        if has_any(["단점", "약점", "리스크", "위험", "불안", "문제", "걱정", "주의"]):
            intents.append("risk")
        if has_any(["성장", "잠재", "유망", "키워", "미래", "장기", "나중"]):
            intents.append("growth")
        if has_any(["가성비", "돈", "가격", "몸값", "이적료", "주급", "예산", "비싸", "싸"]):
            intents.append("finance")
        if has_any(["비교", "누가 더", "vs", "대신", "대체", "보다"]):
            intents.append("compare")
        if not intents:
            intents.append("summary")

        conclusion = "조건부 검토 후보입니다."
        if score >= 80 and fit_score >= 75:
            conclusion = "바로 영입 리스트 상단에 둘 만한 후보입니다."
        elif score >= 70 and (fit_score >= 65 or growth >= 5):
            conclusion = "전술 조건이 맞으면 꽤 설득력 있는 후보입니다."
        elif value_score >= 65 and score >= 60:
            conclusion = "예산형 보강 후보로 볼 수 있습니다."

        if "growth" in intents and growth >= 6 and age <= 23:
            conclusion = "장기 투자형 유망주로 우선 검토할 가치가 큽니다."
        if "finance" in intents and value_score < 35 and value >= 50_000_000:
            conclusion = "성능은 매력적이지만 예산 효율은 조심해야 합니다."

        role_hint = (
            f"{player.get('player_positions')} 기준으로는 {strength_text or '확인 가능한 강점'}을 살리는 쪽이 맞습니다. "
            f"Fit {fit_score:.0f}점이라 기본 적합도는 {'높은 편' if fit_score >= 75 else '보통' if fit_score >= 55 else '낮은 편'}입니다."
        )
        finance_hint = (
            f"시장가치 {money(value)}, 주급 {money(wage)}, 가성비 {value_score:.0f}점입니다. "
            f"예산 압박은 {'큰 편' if value >= 80_000_000 or wage >= 200_000 else '관리 가능한 편' if value_score >= 45 else '따져봐야 하는 편'}입니다."
        )
        growth_hint = (
            f"나이 {age}세, OVR/POT {int(overall)}/{int(potential)}, 성장 여지 {growth:+.0f}입니다. "
            f"{'성장 프리미엄을 줄 수 있습니다.' if growth >= 5 and age <= 24 else '즉시전력 가치 중심으로 봐야 합니다.'}"
        )
        risk_items = []
        if weakness_text:
            risk_items.append(f"약한 수치: {weakness_text}")
        if value >= 80_000_000:
            risk_items.append(f"높은 시장가치: {money(value)}")
        if wage >= 150_000:
            risk_items.append(f"높은 주급: {money(wage)}")
        if growth <= 2 and age >= 28:
            risk_items.append("재판매/성장 여지 제한")
        if not risk_items:
            risk_items.append("수치상 치명적 리스크는 크지 않음")

        sections = [
            f"{player.get('short_name')}에 대한 로컬 미니 분석입니다.\n\n"
            f"결론: {conclusion}",
            (
                f"근거: 종합 스카우팅 점수 {score:.1f}({grade(score)}등급), "
                f"포지션 {player.get('player_positions')}, 핵심 능력 {strength_text or '데이터 부족'}입니다. "
                f"현재 클럽/리그는 {player.get('club_name') or '-'} / {player.get('league_name') or '-'}입니다."
            ),
        ]

        if "usage" in intents or "summary" in intents or "recruit" in intents:
            sections.append(f"활용법: {role_hint}")
        if "recruit" in intents:
            sections.append(
                "영입 판단: 즉시전력 목적이면 OVR와 Fit을 우선 보고, 로테이션/미래 자원 목적이면 성장 여지와 주급 구조를 같이 봐야 합니다."
            )
        if "growth" in intents:
            sections.append(f"성장성: {growth_hint}")
        if "finance" in intents or "recruit" in intents:
            sections.append(f"비용 판단: {finance_hint}")
        if "risk" in intents or "recruit" in intents:
            sections.append(f"주의점: {'; '.join(risk_items)}.")
        if "compare" in intents:
            sections.append(
                "비교 판단: 질문에 비교 대상 선수명이 같이 들어오면 더 정확히 비교할 수 있습니다. 지금은 선택된 선수 단독 기준의 판단입니다."
            )

        if has_any(["공개", "위키", "근거", "출처", "프로필"]):
            note = public_note()
            if note:
                sections.append(note.strip())

        return "\n\n".join(sections)

    if is_saved_squad_fit_question(question):
        fit_brief = saved_squad_fit_brief(player)
        if fit_brief:
            return fit_brief

    if is_saved_squad_role_question(question):
        role_brief = saved_squad_role_brief(player, question)
        if role_brief:
            return role_brief

    if wikipedia_question:
        return public_profile_answer()

    if any(keyword in question_lower for keyword in ["주발", "preferred", "foot", "발은", "왼발", "오른발"]):
        preferred_foot = player.get("preferred_foot") or "데이터 없음"
        weak_foot = player.get("weak_foot") or "데이터 없음"
        return (
            f"{player.get('short_name')}의 주발은 {preferred_foot}입니다.\n\n"
            f"CSV 기준 약발 평점은 {weak_foot}이고, 포지션은 {player.get('player_positions')}입니다. "
            "주발 정보는 측면 배치, 인버티드 윙어 활용, 빌드업 방향을 판단할 때 우선 확인하면 좋습니다."
        )

    if any(keyword in question_lower for keyword in ["약발", "weak foot", "weak_foot"]):
        return (
            f"{player.get('short_name')}의 약발 평점은 {player.get('weak_foot') or '데이터 없음'}입니다.\n\n"
            f"주발은 {player.get('preferred_foot') or '데이터 없음'}이고, 개인기 평점은 {player.get('skill_moves') or '데이터 없음'}입니다."
        )

    if any(keyword in question_lower for keyword in ["개인기", "스킬", "skill move", "skill_moves"]):
        return (
            f"{player.get('short_name')}의 개인기 평점은 {player.get('skill_moves') or '데이터 없음'}입니다.\n\n"
            f"드리블 수치는 {player.get('dribbling') or '데이터 없음'}, 주발은 {player.get('preferred_foot') or '데이터 없음'}입니다."
        )

    rich_mini_keywords = [
        "영입",
        "데려",
        "사야",
        "계약",
        "보강",
        "추천",
        "어때",
        "필요",
        "왜",
        "주전",
        "후보",
        "어떻게",
        "활용",
        "기용",
        "배치",
        "운용",
        "단점",
        "약점",
        "리스크",
        "위험",
        "불안",
        "문제",
        "걱정",
        "주의",
        "성장",
        "잠재",
        "유망",
        "가성비",
        "비교",
        "대체",
    ]
    exact_team_info_question = has_any(["소속팀", "현재 팀", "클럽", "club"]) and not has_any(
        ["우리 팀", "영입", "필요", "보강", "추천", "어때", "활용", "기용", "배치"]
    )
    if has_any(rich_mini_keywords) and not exact_team_info_question:
        return local_mini_scouting_answer()

    if any(keyword in question_lower for keyword in ["소속팀", "클럽", "팀", "club"]):
        return (
            f"{player.get('short_name')}의 현재 소속팀은 {player.get('club_name') or '-'}이고, "
            f"소속 리그는 {player.get('league_name') or '-'}입니다.\n\n"
            f"국적은 {player.get('nationality_name')}, 지역은 {player.get('region')}입니다."
        )

    if location_question:
        return (
            f"{player.get('short_name')}의 지역/적응 평가는 국적 {player.get('nationality_name')}, "
            f"지역 {player.get('region')}, 현재 리그 {player.get('league_name') or '-'}를 proxy로 봅니다.\n\n"
            "현재 CSV에는 고향, 출생지, 집 주소, 현재 거주지 같은 직접 컬럼이 없습니다. "
            "특히 집 주소나 실제 거주지는 사생활 정보라 공개 데이터로 확인되지 않으면 답하지 않는 것이 맞습니다.\n\n"
            "실제 영입 전에는 공개 프로필의 출생지, 성장 리그, 언어권, 가족 동반 여부를 추가 확인해야 합니다. "
            "데이터 기준으로는 같은 지역/유사 리그 경험이 많을수록 초기 적응 리스크를 낮게 평가하는 방식이 적절합니다."
        )

    if tactic_question:
        return (
            f"{player.get('short_name')}은 {player.get('player_positions')}에서 활용 가능한 자원입니다.\n\n"
            f"현재 포지션 Fit은 {fit_score:.0f}점이고, 핵심 능력은 {strength_text or '주요 능력치 확인 필요'}입니다. "
            f"강한 능력치를 기준으로 보면 전방 압박/공간 침투/온더볼 역할 중 데이터가 맞는 쪽에 우선 배치하는 것이 좋습니다.\n\n"
            f"주의할 부분은 {weakness_text or '특정 약점 데이터 부족'}입니다. 이 약점이 팀 전술의 핵심 요구사항과 겹치면 영입 우선순위를 낮춰야 합니다."
        )

    if any(keyword in question_lower for keyword in ["가성비", "몸값", "이적료", "주급", "비싸", "싸", "예산", "value", "wage", "fee"]):
        return (
            f"{player.get('short_name')}의 시장가치는 {money(value)}, 주급은 {money(wage)}입니다.\n\n"
            f"가성비 점수는 {value_score:.0f}점이고, 종합 스카우팅 점수는 {score:.1f}입니다. "
            "즉시전력 기여도가 높아도 시장가치와 주급이 높으면 예산 효율은 낮게 잡힙니다.\n\n"
            "추천 판단은 팀 예산에 따라 달라집니다. 빅클럽 즉시전력 목적이면 성능 중심으로, 제한 예산이면 동일 포지션의 낮은 몸값 후보와 비교해야 합니다."
        )

    if any(keyword in question_lower for keyword in ["잠재", "강점", "장점", "성장", "potential", "strength", "upside"]):
        return (
            f"{player.get('short_name')}의 잠재력은 OVR {int(overall)}에서 POT {int(potential)}로, 성장 여지는 {growth:+.0f}입니다.\n\n"
            f"핵심 강점은 {strength_text}입니다. "
            f"포지션이 {player.get('player_positions')}인 점을 고려하면 현재 전술 적합도 점수는 {float(player.get('fit_score', 0)) * 100:.0f}점 수준입니다.\n\n"
            "데이터상으로는 즉시전력과 성장성을 함께 보는 후보이며, 실제 영입 판단에서는 경기 영상과 부상 이력 확인이 추가로 필요합니다."
        )

    if any(keyword in question_lower for keyword in ["리스크", "risk", "위험", "약점", "단점", "불안", "문제"]):
        risks = []
        if value >= 80_000_000:
            risks.append(f"시장가치가 {money(value)}로 높아 이적료 부담이 큽니다")
        if wage >= 150_000:
            risks.append(f"주급이 {money(wage)}라 급여 구조에 부담이 될 수 있습니다")
        if growth <= 2 and age >= 27:
            risks.append("성장 여지가 제한적이라 재판매 가치가 크지 않을 수 있습니다")
        if float(player.get("value_score", 0) or 0) < 0.1:
            risks.append("가성비 점수가 낮아 예산 효율 관점에서는 우선순위가 떨어질 수 있습니다")
        if not risks:
            risks.append("데이터상 큰 재정 리스크는 낮지만, 실제 경기력 변동성과 리그 적응은 별도 확인이 필요합니다")
        return (
            f"{player.get('short_name')} 영입의 가장 큰 리스크는 {risks[0]}.\n\n"
            f"추가 리스크: {'; '.join(risks[1:]) or '공개 데이터만으로는 추가 리스크를 단정하기 어렵습니다.'}"
            f"{public_note()}"
        )

    return local_mini_scouting_answer()


def generate_openai_chat_answer(player: dict, question: str, wikipedia_context: dict | None = None) -> str:
    api_key = get_openai_api_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    if wikipedia_context is None:
        wikipedia_context = fetch_wikipedia_context(player)
    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": (
                    "너는 축구 클럽 스카우팅 의사결정을 돕는 채팅형 AI Agent다. "
                    "사용자는 특정 선수를 클릭한 뒤 자유롭게 질문한다. "
                    "FC26 수치, 선수 기본 정보, Wikipedia 공개 정보를 함께 사용해 한국어로 답한다. "
                    "birth_place/current_city 컬럼은 없으므로 nationality_name, league_name, club_name, region을 지역/적응 proxy로만 해석한다. "
                    "질문이 '치명적인 단점', '숨은 리스크', '팀 분위기'처럼 정성적이면 공개 이력과 수치 데이터를 연결해 스카우팅 관점으로 추론한다. "
                    "단, Wikipedia 요약에 없는 발언이나 특정 인물의 인용문은 절대 만들지 않는다. "
                    "공개 정보에서 확인되는 내용만 근거로 삼고, 추론은 추론이라고 표시한다. "
                    "Wikipedia 정보를 사용했다면 마지막에 '근거:' 줄로 URL을 붙인다. "
                    "답변은 4문단 이내로, 단순 수치 나열보다 영입 의사결정에 바로 쓸 수 있는 판단 중심으로 작성한다."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"선수 데이터: {compact_player_context(player)}\n\n"
                    f"{format_wikipedia_context(wikipedia_context)}\n\n"
                    f"질문: {question}"
                ),
            },
        ],
        "max_output_tokens": 950,
    }
    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=25,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("output_text"):
        return data["output_text"].strip()

    chunks = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(content["text"])
    if not chunks:
        raise RuntimeError("OpenAI response did not include text")
    return "\n".join(chunks).strip()


def answer_scouting_question(player: dict, question: str) -> tuple[str, str]:
    if is_greeting_question(question):
        return greeting_answer(), "local_greeting"

    try:
        return generate_openai_chat_answer(player, question), "openai"
    except Exception:
        return generate_template_chat_answer(player, question), "local_mini_fallback"


def answer_scouting_question_with_middleware(
    player: dict,
    question: str,
    session_id: str = "default",
) -> tuple[str, str, dict]:
    session = get_session(session_id)
    summary = summarization_middleware(session)

    if is_greeting_question(question):
        answer = greeting_answer()
        session["messages"].append({"role": "user", "content": question})
        session["messages"].append({"role": "assistant", "content": answer})
        return answer, "local_greeting", middleware_state(session)

    if is_saved_squad_fit_question(question):
        fit_brief = saved_squad_fit_brief(player)
        if fit_brief:
            session["messages"].append({"role": "user", "content": question})
            session["messages"].append({"role": "assistant", "content": fit_brief})
            return fit_brief, "saved_squad", middleware_state(session)

    if is_saved_squad_role_question(question):
        role_brief = saved_squad_role_brief(player, question)
        if role_brief:
            session["messages"].append({"role": "user", "content": question})
            session["messages"].append({"role": "assistant", "content": role_brief})
            return role_brief, "saved_squad", middleware_state(session)

    wikipedia_context = {}
    try:
        tool_call_limit_middleware(session)
        approval = human_in_the_loop_middleware(
            session,
            "fetch_wikipedia_context",
            {
                "player_id": player.get("player_id"),
                "short_name": player.get("short_name"),
            },
        )
        if approval["approved"]:
            wikipedia_context = fetch_wikipedia_context(player)
    except Exception:
        wikipedia_context = {}

    try:
        model_call_limit_middleware(session)
        context_question = question
        if summary:
            context_question = f"이전 대화 요약: {summary}\n\n현재 질문: {question}"
        answer = generate_openai_chat_answer(player, context_question, wikipedia_context=wikipedia_context)
        source = "openai"
    except Exception as exc:
        if str(exc).startswith("[modelCallLimit]"):
            answer = str(exc)
            source = "middleware_blocked"
        else:
            answer = generate_template_chat_answer(player, question)
            source = "local_mini_fallback"

    session["messages"].append({"role": "user", "content": question})
    session["messages"].append({"role": "assistant", "content": answer})
    return answer, source, middleware_state(session)
