from __future__ import annotations

import os
from urllib.parse import quote

import requests

from app.core.config import ENV_PATH

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


def fetch_wikipedia_context(player: dict) -> dict:
    name = player.get("long_name") or player.get("short_name") or ""
    nationality = player.get("nationality_name") or ""
    query = f"{name} footballer {nationality}".strip()

    for language in ("en", "ko"):
        try:
            title = wikipedia_search_title(query, language=language)
            if title:
                summary = wikipedia_summary(title, language=language)
                if summary.get("extract"):
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

    def public_note() -> str:
        context = fetch_wikipedia_context(player)
        if not context.get("extract"):
            return ""
        return (
            f"\n\n공개 이력 참고: {context.get('extract')[:450]}"
            f"\n근거: {context.get('url')}"
        )

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

    if any(keyword in question_lower for keyword in ["소속팀", "클럽", "팀", "club"]):
        return (
            f"{player.get('short_name')}의 현재 소속팀은 {player.get('club_name') or '-'}이고, "
            f"소속 리그는 {player.get('league_name') or '-'}입니다.\n\n"
            f"국적은 {player.get('nationality_name')}, 지역은 {player.get('region')}입니다."
        )

    if any(keyword in question_lower for keyword in ["전술", "역할", "포지션", "fit", "role", "tactic", "어디", "활용"]):
        return (
            f"{player.get('short_name')}은 {player.get('player_positions')}에서 활용 가능한 자원입니다.\n\n"
            f"현재 포지션 Fit은 {fit_score:.0f}점이고, 핵심 능력은 {strength_text or '주요 능력치 확인 필요'}입니다. "
            f"강한 능력치를 기준으로 보면 전방 압박/공간 침투/온더볼 역할 중 데이터가 맞는 쪽에 우선 배치하는 것이 좋습니다.\n\n"
            f"주의할 부분은 {weakness_text or '특정 약점 데이터 부족'}입니다. 이 약점이 팀 전술의 핵심 요구사항과 겹치면 영입 우선순위를 낮춰야 합니다."
        )

    if any(keyword in question_lower for keyword in ["지역", "적응", "고향", "사는", "국가", "국적", "리그", "문화", "언어"]):
        return (
            f"{player.get('short_name')}의 지역/적응 평가는 국적 {player.get('nationality_name')}, "
            f"지역 {player.get('region')}, 현재 리그 {player.get('league_name') or '-'}를 proxy로 봅니다.\n\n"
            "현재 랭킹 점수에는 지역 Fit을 반영하지 않습니다. CSV에 고향/거주지 직접 컬럼은 없어서, 실제 영입 전에는 출생지, 성장 리그, 언어권, 가족 동반 여부를 추가 확인해야 합니다.\n\n"
            "데이터 기준으로는 같은 지역/유사 리그 경험이 많을수록 초기 적응 리스크를 낮게 평가하는 방식이 적절합니다."
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

    return (
        f"{player.get('short_name')}에 대한 질문을 스카우팅 관점으로 해석하면, 현재는 종합 점수 {score:.1f}의 "
        f"{grade(score)}등급 후보입니다.\n\n"
        f"핵심 근거는 OVR/POT {int(overall)}/{int(potential)}, 포지션 {player.get('player_positions')}, "
        f"강점 {strength_text or '주요 능력치 확인 필요'}입니다. "
        f"클럽/리그는 {player.get('club_name') or '-'} / {player.get('league_name') or '-'}이고, "
        f"국적/지역은 {player.get('nationality_name')} / {player.get('region')}입니다.\n\n"
        f"영입 판단은 목적에 따라 갈립니다. 즉시전력이라면 OVR와 강점 능력치를, 장기 투자라면 성장 여지 {growth:+.0f}와 나이 {age}세를, "
        f"예산형 영입이라면 시장가치 {money(value)}와 주급 {money(wage)}를 우선 비교하는 것이 좋습니다."
        f"{public_note()}"
    )


def generate_openai_chat_answer(player: dict, question: str) -> str:
    api_key = get_openai_api_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
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
    try:
        return generate_openai_chat_answer(player, question), "openai"
    except Exception:
        return generate_template_chat_answer(player, question), "template_fallback"
