"""POST /api/query — 프론트엔드가 호출하는 유일한 진입점.

teammate(권도윤)의 aiagent SSE 포맷(docs/api.md)에 맞춘다. 우리 agent도
자체 `/api/v1/query/stream`이 있지만, 그건 그대로 프록시하지 않고
(agent 응답을 우리 guardrail로 재검증·재실행하는 방어 로직이 있기 때문에)
같은 "와이어 포맷"만 재사용해서 우리 파이프라인 진행 상황을 내보낸다.

포맷 요약 (agent와 동일):

- SSE `event:` 줄은 쓰지 않는다. 매 줄이 `data: <JSON>\n\n` 하나뿐이고,
  그 JSON 안에 "event" 키로 종류를 구분한다.
- `event: "node"` — 노드 1개 완료. `node`(노드명), `data`(그 노드 결과, JSON 문자열)
- `event: "done"` — 최종 완료. `data`(최종 answer, JSON 문자열)
- `event: "error"` — 오류. `data`(사유 문자열)

우리 파이프라인은 agent의 6노드(schema_link~format)와 다르게 구성되어 있어
아래 3개 노드로 진행 상황을 알린다: `generate`(agent에게 SQL 요청) →
`validate`(guardrail 재검증) → `execute`(우리 자체 DB 재실행).
"""

import json
from collections.abc import AsyncGenerator

import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.db.database import run_readonly_query
from app.schemas.query import QueryRequest
from app.services.agent_client import AgentQueryError, ask_ai_agent
from app.services.guardrail import GuardrailError, validate_sql
from app.services.session_store import append_turn, get_history

router = APIRouter()


def _emit(event: str, **fields) -> str:
    """{"event": ..., **fields} 를 한 줄 `data: <JSON>\\n\\n` 으로 내보낸다."""
    payload = {"event": event, **fields}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _node(name: str, data: dict) -> str:
    """agent 포맷과 동일하게, 노드 결과(dict)를 JSON 문자열로 이중 인코딩해서 담는다."""
    return _emit("node", node=name, data=json.dumps(data, ensure_ascii=False))


def _rows_to_columns(rows: list[dict]) -> tuple[list[str], list[list]]:
    """우리 DB 조회 결과([{컬럼: 값}, ...])를 agent 포맷(columns/rows 분리)으로 변환."""
    columns = list(rows[0].keys())
    row_values = [list(row.values()) for row in rows]
    return columns, row_values


async def _query_stream(req: QueryRequest) -> AsyncGenerator[str, None]:
    """실제 요청 처리 파이프라인. 각 단계마다 node 이벤트를 하나씩 내보낸다."""
    try:
        # 1) AI agent에게 SQL 생성을 요청한다.
        #    후속 질문 지원을 위해 이 세션의 이전 대화 히스토리는 우리 쪽에만 유지한다
        #    (agent 스펙에 session_id/history 필드가 없음).
        history = get_history(req.session_id)
        try:
            agent_result = await ask_ai_agent(req.question, history)
        except AgentQueryError as e:
            # agent가 스스로 "이 요청은 처리할 수 없다"고 판단한 경우
            # (예: 안전하지 않은 요청, 모호한 질문).
            yield _emit("error", data=e.message)
            return
        except httpx.HTTPError:
            # agent 서버가 꺼져 있거나 응답이 비정상(4xx/5xx)인 경우.
            yield _emit("error", data="AI agent 서버에 연결할 수 없습니다. agent가 실행 중인지 확인해주세요.")
            return

        yield _node("generate", {"sql": agent_result.sql})

        # 2) AI agent가 만든 SQL을 백엔드 자체 가드레일로 한 번 더 검증한다.
        #    (SELECT 외 쿼리 차단, LIMIT 자동 추가) — 신뢰성 문제 대응.
        try:
            safe_sql = validate_sql(agent_result.sql)
        except GuardrailError as e:
            yield _emit("error", data=e.message)
            return

        yield _node("validate", {"validation": {"ok": True, "errors": []}})

        # 3) 검증을 통과한 SQL만 text2sql_reader(읽기 전용) 계정으로 실행한다.
        try:
            rows = run_readonly_query(safe_sql)
        except Exception:
            yield _emit("error", data="쿼리 실행 중 오류가 발생했습니다.")
            return

        if not rows:
            yield _emit("error", data="조건에 맞는 결과가 없습니다.")
            return

        columns, row_values = _rows_to_columns(rows)
        yield _node("execute", {"result": {"columns": columns, "rows": row_values, "truncated": False}})

        # 4) 이번 턴을 세션 히스토리에 저장해서, 다음 질문("그 중에 1위만" 등)에
        #    이 맥락을 이어서 넘길 수 있게 한다.
        append_turn(req.session_id, question=req.question, sql=safe_sql, summary=agent_result.summary)

        final_answer = {
            "summary": agent_result.summary,
            "table": {"columns": columns, "rows": row_values},
            "sql": safe_sql,
            "disclaimer": "",
        }
        yield _emit("done", data=json.dumps(final_answer, ensure_ascii=False))

    except Exception:
        # 위 단계들에서 예상하지 못한 예외가 나도 스트림이 그냥 끊기지 않고
        # 반드시 error 이벤트로 마무리되도록 하는 최종 방어선.
        yield _emit("error", data="예상치 못한 오류가 발생했습니다.")


@router.post("/api/query")
async def query(req: QueryRequest) -> StreamingResponse:
    """프론트엔드가 호출하는 유일한 엔드포인트. 응답은 SSE 스트림이다."""
    return StreamingResponse(_query_stream(req), media_type="text/event-stream")
