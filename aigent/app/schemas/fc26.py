from __future__ import annotations

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
