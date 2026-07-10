from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Any


sessions: dict[str, dict[str, Any]] = {}


def get_session(session_id: str) -> dict[str, Any]:
    if session_id not in sessions:
        sessions[session_id] = {
            "id": session_id,
            "logs": [],
            "model_call_count": 0,
            "tool_call_count": 0,
            "summaries": [],
            "pending_approval": None,
            "messages": [],
            "config": {
                "modelRunLimit": 5,
                "toolRunLimit": 3,
                "summarizeThreshold": 4,
                "requireApproval": False,
            },
        }
    return sessions[session_id]


def add_log(
    session: dict[str, Any],
    middleware: str,
    level: str,
    message: str,
    detail: str | None = None,
) -> dict[str, Any]:
    log = {
        "id": f"{time.time()}-{uuid.uuid4().hex[:6]}",
        "middleware": middleware,
        "level": level,
        "message": message,
        "detail": detail,
        "ts": datetime.now().strftime("%p %I:%M:%S").replace("AM", "오전").replace("PM", "오후"),
    }
    session["logs"].append(log)
    return log


def model_call_limit_middleware(session: dict[str, Any]) -> None:
    session["model_call_count"] += 1
    limit = int(session["config"].get("modelRunLimit", 5))
    count = session["model_call_count"]

    if count > limit:
        add_log(
            session,
            "modelCallLimit",
            "block",
            f"LLM 호출 한도 초과 ({count}/{limit})",
            f"설정된 최대 호출 횟수({limit})를 초과해 OpenAI 답변 생성을 중단합니다.",
        )
        raise RuntimeError(f"[modelCallLimit] LLM 호출 한도({limit}회)를 초과했습니다.")

    add_log(
        session,
        "modelCallLimit",
        "pass",
        f"LLM 호출 허용 ({count}/{limit})",
        f"남은 호출 가능 횟수: {limit - count}회",
    )


def tool_call_limit_middleware(session: dict[str, Any]) -> None:
    session["tool_call_count"] += 1
    limit = int(session["config"].get("toolRunLimit", 3))
    count = session["tool_call_count"]

    if count > limit:
        add_log(
            session,
            "toolCallLimit",
            "block",
            f"Tool 호출 한도 초과 ({count}/{limit})",
            "Wikipedia 공개 정보 조회 횟수가 한도를 초과했습니다.",
        )
        raise RuntimeError(f"[toolCallLimit] Tool 호출 한도({limit}회)를 초과했습니다.")

    add_log(
        session,
        "toolCallLimit",
        "pass",
        f"Tool 호출 허용 ({count}/{limit})",
        f"남은 Tool 호출 가능 횟수: {limit - count}회",
    )


def summarization_middleware(session: dict[str, Any]) -> str | None:
    threshold = int(session["config"].get("summarizeThreshold", 4))
    msg_count = len(session["messages"])

    if msg_count > 0 and msg_count % threshold == 0:
        recent = session["messages"][-threshold:]
        lines = []
        for message in recent:
            content = str(message.get("content", "")).replace("\n", " ").strip()
            lines.append(f"{message.get('role')}: {content[:120]}")

        summary_text = " / ".join(lines)
        session["summaries"].append({"at": msg_count, "text": summary_text})
        add_log(
            session,
            "summarization",
            "info",
            f"대화 요약 실행 (메시지 {msg_count}개 -> 요약본 생성)",
            f"요약: {summary_text}",
        )
        return summary_text

    remainder = threshold if msg_count == 0 else threshold - (msg_count % threshold or threshold)
    add_log(
        session,
        "summarization",
        "pass",
        f"요약 불필요 (현재 {msg_count}개 / 기준 {threshold}개)",
        f"{remainder}개 더 쌓이면 자동 요약됩니다.",
    )
    return None


def human_in_the_loop_middleware(
    session: dict[str, Any],
    tool_name: str,
    tool_args: dict[str, Any],
) -> dict[str, Any]:
    if not session["config"].get("requireApproval", False):
        add_log(
            session,
            "humanInTheLoop",
            "pass",
            "자동 승인 (Human-in-the-Loop 비활성화)",
            f'requireApproval=false: 도구 "{tool_name}" 자동 실행',
        )
        return {"approved": True, "auto": True}

    session["pending_approval"] = {
        "toolName": tool_name,
        "toolArgs": tool_args,
        "status": "pending",
        "requestedAt": datetime.now().isoformat(),
    }
    add_log(
        session,
        "humanInTheLoop",
        "warn",
        f'사람 승인 대기 중 - Tool: "{tool_name}"',
        f"실행 인자: {tool_args}",
    )

    timeout_sec, interval_sec, elapsed = 30.0, 0.2, 0.0
    while elapsed < timeout_sec:
        time.sleep(interval_sec)
        elapsed += interval_sec
        approval = session.get("pending_approval")
        if approval is None or approval.get("status") != "pending":
            break

    result = session.get("pending_approval")
    session["pending_approval"] = None

    if result and result.get("status") == "approved":
        add_log(session, "humanInTheLoop", "info", f'사람이 승인함 - Tool: "{tool_name}"', "도구 실행을 허가합니다.")
        return {"approved": True, "auto": False}

    add_log(session, "humanInTheLoop", "block", f'사람이 거절함 - Tool: "{tool_name}"', "도구 실행이 거부되었습니다.")
    return {"approved": False, "auto": False}


def middleware_state(session: dict[str, Any]) -> dict[str, Any]:
    return {
        "sessionId": session["id"],
        "config": session["config"],
        "modelCallCount": session["model_call_count"],
        "toolCallCount": session["tool_call_count"],
        "messageCount": len(session["messages"]),
        "summaryCount": len(session["summaries"]),
        "summaries": session["summaries"],
        "pendingApproval": session["pending_approval"],
        "recentLogs": session["logs"][-20:],
    }


def update_session_config(session_id: str, config: dict[str, Any]) -> dict[str, Any]:
    session = get_session(session_id)
    session["config"].update(config)
    return session["config"]


def approve_session(session_id: str, approved: bool) -> bool:
    session = get_session(session_id)
    if not session["pending_approval"]:
        return False
    session["pending_approval"]["status"] = "approved" if approved else "rejected"
    return True


def reset_session(session_id: str) -> None:
    sessions.pop(session_id, None)
