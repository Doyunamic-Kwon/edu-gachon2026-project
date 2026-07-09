"""HTTP 라우터 — 자연어 질의를 받아 에이전트 결과를 반환한다.

POST /api/v1/query         동기 응답 (QueryResponse)
POST /api/v1/query/stream  SSE 로 노드 진행 상황 스트리밍
"""
from __future__ import annotations

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.graph.builder import NODE_NAMES, build_graph
from app.graph.state import initial_state
from app.schemas.query import QueryRequest, QueryResponse, StreamEvent

router = APIRouter()
graph = build_graph()


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest) -> QueryResponse:
    """질의를 처리해 요약·표·SQL 을 반환한다.

    입력: QueryRequest(question)
    출력: QueryResponse(summary, columns, rows, sql, difficulty, model, error)
    """
    state = await graph.ainvoke(initial_state(req.question))
    answer = state.get("answer", {})
    table = answer.get("table", {})
    return QueryResponse(
        summary=answer.get("summary", ""),
        columns=table.get("columns", []),
        rows=table.get("rows", []),
        sql=state.get("sql", ""),
        difficulty=state.get("difficulty", ""),
        model=state.get("model", ""),
        error=state.get("error", ""),
    )


@router.post("/query/stream")
async def query_stream(req: QueryRequest):
    """각 노드 완료 시점을 SSE 로 흘려보낸다 (event: node → done).

    입력: QueryRequest(question)
    출력: text/event-stream (StreamEvent JSON)
    """

    async def gen():
        async for event in graph.astream_events(initial_state(req.question), version="v2"):
            if event.get("event") == "on_chain_end" and event.get("name") in NODE_NAMES:
                ev = StreamEvent(
                    event="node",
                    node=event["name"],
                    data=json.dumps(event.get("data", {}).get("output", {}), ensure_ascii=False, default=str),
                )
                yield f"data: {ev.model_dump_json()}\n\n"
        final = await graph.ainvoke(initial_state(req.question))
        done = StreamEvent(event="done", data=json.dumps(final.get("answer", {}), ensure_ascii=False, default=str))
        yield f"data: {done.model_dump_json()}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
