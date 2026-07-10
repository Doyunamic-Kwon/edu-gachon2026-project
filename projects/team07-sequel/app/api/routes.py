"""HTTP 컨트롤러 — 자연어 질의 엔드포인트. 얇게 유지(요청 수신 → 서비스 위임 → 응답).

POST /api/v1/query         동기 응답 (QueryResponse)
POST /api/v1/query/stream  SSE 로 노드 진행 상황 스트리밍
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import query_service

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest) -> QueryResponse:
    """질의를 처리해 요약·표·SQL 을 반환한다."""
    return await query_service.run(req.question)


@router.post("/query/stream")
async def query_stream(req: QueryRequest):
    """각 노드 완료 시점을 SSE(text/event-stream) 로 흘려보낸다."""

    async def gen():
        async for event in query_service.stream(req.question):
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
