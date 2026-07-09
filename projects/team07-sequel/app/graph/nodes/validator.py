"""validator 노드 — 실행 전 SQL 을 검증한다 (sqlglot).

문법 파싱, SELECT 만 허용, 금지 키워드(INSERT/UPDATE/DELETE/DROP 등),
화이트리스트 밖 테이블/컬럼, 위험 패턴(전체 테이블 조회 등)을 점검한다.
(도구: tools.sql_validator)

입력(state): sql, schema
출력(state): validation({"ok": bool, "errors": list[str]})
"""
from app.graph.state import AgentState


def validate(state: AgentState) -> dict:
    # TODO(tool 단계): tools.sql_validator.validate_sql(state["sql"], state["schema"])
    return {"validation": {"ok": True, "errors": []}}
