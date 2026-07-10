"""백엔드 <-> AI agent 연동 지점.

2026-07-10 업데이트: 팀원의 aiagent 브랜치가 main에 병합되고, 실제 Cloud Run
서비스(text2sql-agent)로 배포된 것을 확인해서 mock을 실제 HTTP 호출로 교체했다.
(이전에 한 번 "실제 스펙"으로 보고 연동했다가, 그게 강사 측 벤치마킹용 예시
코드였음이 드러나 mock으로 롤백한 적이 있다 — 이번엔 실제 코드(app/main.py,
app/api/routes.py, app/schemas/query.py)를 직접 확인하고 진행한 것이라 다르다.)

실제 agent 응답에는 summary/columns/rows/sql/difficulty/model/error가 들어있지만,
우리는 sql과 summary만 쓴다. agent가 이미 실행한 columns/rows는 신뢰하지 않고
버린다 — 백엔드가 자체 guardrail로 재검증하고 자체 읽기 전용 DB 커넥션으로
다시 실행하는 defense-in-depth 설계를 그대로 유지하기 위함이다 (query.py 참고).

agent_client.py 하나만 교체하면 되도록 설계해뒀던 대로, main.py/query.py 등
나머지 코드는 이번에도 손대지 않았다.
"""

import httpx

from app.core.config import settings
from app.schemas.query import AgentResult


class AgentError(Exception):
    """AI agent가 자체적으로 처리 실패를 알려온 경우 (응답의 error 필드가 채워짐)."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


async def ask_ai_agent(question: str, history: list[dict]) -> AgentResult:
    """AI agent(Cloud Run)에 실제 HTTP로 SQL 생성을 요청한다.

    주의: 지금 agent의 /api/v1/query는 question만 받고 세션/히스토리 개념이
    없다. 그래서 history는 아직 agent에 전달하지 못하고 있다 (우리 쪽
    session_store에는 계속 쌓이지만, agent의 SQL 생성에는 아직 반영 안 됨).
    agent가 세션 파라미터를 지원하게 되면 이 함수만 다시 고치면 된다.
    """
    async with httpx.AsyncClient(base_url=settings.AI_AGENT_BASE_URL, timeout=60) as client:
        resp = await client.post("/api/v1/query", json={"question": question})
        resp.raise_for_status()
        data = resp.json()

    if data.get("error"):
        raise AgentError(data["error"])

    return AgentResult(sql=data.get("sql", ""), summary=data.get("summary", ""))
