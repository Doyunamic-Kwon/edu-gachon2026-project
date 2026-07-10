"""executor 노드 — 검증된 SQL 을 읽기전용으로 실행하고 결과를 포맷한다.

SELECT 만, LIMIT·타임아웃 강제. 결과 형태(scalar/table/chart/text)를 판별해 반환.
(도구: tools.sql_executor → core.db 읽기전용 엔진)

입력(state): sql
출력(state): result({"columns", "rows", "format", "truncated"})
"""
from app.graph.state import AgentState
from app.tools.sql_executor import execute_sql


def execute(state: AgentState) -> dict:
    result = execute_sql(state.get("sql", ""))
    return {"result": result.model_dump()}
