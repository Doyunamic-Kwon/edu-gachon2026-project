"""API 요청/응답 DTO (Pydantic).

HTTP 경계에서 쓰는 스키마. 그래프 내부 상태(AgentState)와는 분리한다.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """자연어 질의 요청.

    입력: question(1~2000자)
    """

    question: str = Field(..., min_length=1, max_length=2000)


class QueryResponse(BaseModel):
    """질의 처리 결과 (동기 응답).

    출력: 자연어 요약 + 표(columns/rows) + 실행 SQL + 라우팅 메타.
    """

    summary: str = ""
    columns: list[str] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)
    sql: str = ""
    difficulty: str = ""
    model: str = ""
    error: str = ""


class StreamEvent(BaseModel):
    """SSE 이벤트 한 건.

    event: "node"(노드 완료) | "done"(최종) | "error"
    node:  노드 이름 (event=="node" 일 때)
    data:  JSON 직렬화된 페이로드
    """

    event: str = "node"
    node: str = ""
    data: str = ""
