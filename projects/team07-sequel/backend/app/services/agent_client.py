"""백엔드 <-> AI agent 연동 지점.

    POST {AI_AGENT_BASE_URL}/api/v1/query
    요청: {"question": str}
    응답: {"summary", "columns", "rows", "sql", "difficulty", "model", "error"}

연동하면서 주의한 점:

- agent 쪽 스펙에는 session_id/history 필드가 없다. 그래서 후속 질문 맥락은
  지금은 우리 backend의 session_store에만 쌓이고, agent에는 아직 넘기지
  않는다. agent가 나중에 history를 지원하게 되면 여기서 같이 보내면 된다.
- agent 응답에는 이미 실행된 rows/columns도 들어있지만, 우리는 그 값을
  쓰지 않는다. agent가 만든 `sql` 문자열만 가져와서 우리 쪽
  guardrail(validate_sql)로 다시 검증하고, 우리 자체 읽기 전용 계정으로
  재실행한다 — agent 서버가 어떤 권한/커넥션으로 실행했는지 우리가
  보장할 수 없으니, 실제 DB 접근은 항상 우리 쪽에서 한 번 더 통제한다.
- agent는 아직 스켈레톤 상태라 `sql: "SELECT 1"` 같은 placeholder가
  돌아올 수 있다. 정상 동작이며, agent 쪽 로직이 채워지면 자동으로
  실제 결과로 바뀐다.
"""

import httpx

from app.core.config import settings
from app.schemas.query import AgentResult


class AgentQueryError(Exception):
    """agent가 `error` 필드를 채워서 응답했을 때 (예: 안전하지 않은 요청으로 거절됨)."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


async def ask_ai_agent(question: str, history: list[dict]) -> AgentResult:
    async with httpx.AsyncClient(base_url=settings.AI_AGENT_BASE_URL, timeout=60) as client:
        resp = await client.post("/api/v1/query", json={"question": question})
        resp.raise_for_status()
        data = resp.json()

    if data.get("error"):
        raise AgentQueryError(data.get("summary") or data["error"])

    return AgentResult(sql=data["sql"], summary=data["summary"])
