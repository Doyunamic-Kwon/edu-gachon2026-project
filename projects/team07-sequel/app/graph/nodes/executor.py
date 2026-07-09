"""executor 노드 — 검증된 SQL 을 읽기전용으로 실행하고 결과를 포맷한다.

SELECT 만, LIMIT·타임아웃 강제. 결과 형태(scalar/table/chart/text)를 판별해 반환.
(도구: tools.sql_executor → core.db 읽기전용 엔진)

입력(state): sql
출력(state): result({"columns": list, "rows": list, "format": str, "truncated": bool})
"""
from app.graph.state import AgentState


def execute(state: AgentState) -> dict:
    # TODO(tool 단계): tools.sql_executor.execute_sql(state["sql"]) 후 결과 형태 판별
    return {"result": {"columns": [], "rows": [], "format": "table", "truncated": False}}
