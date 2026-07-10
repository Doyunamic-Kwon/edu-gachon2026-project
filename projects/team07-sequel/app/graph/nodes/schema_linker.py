"""schema_link 노드 — 정규화된 질문/키워드로 스키마·값을 링크한다.

관련 테이블만 임베딩으로 축소하고(schema_retriever), 키워드를 실제 DB 값으로
확정한다(value_retriever). SQL 생성이 "작고 정확한 컨텍스트"만 보게 한다.
(도구: tools.schema_retriever, tools.value_retriever)

입력(state): normalized_question(없으면 question), keywords, time_range
출력(state): schema(축소 DDL+조인+값힌트+기간), tables, joins, value_hints, unresolved
"""
from app.graph.state import AgentState
from app.tools.schema_retriever import retrieve_schema
from app.tools.value_retriever import retrieve_values


def schema_link(state: AgentState) -> dict:
    question = state.get("normalized_question") or state["question"]
    keywords = state.get("keywords") or []

    schema_res = retrieve_schema(question)
    value_res = retrieve_values(keywords, schema_res.tables)

    parts = [schema_res.ddl]
    if schema_res.joins:
        parts.append("# 조인 경로\n" + "\n".join(schema_res.joins))
    if value_res.hints:
        parts.append("# 값 매칭\n" + "\n".join(
            f"{h.keyword} → {h.column} = {h.value} ({h.how})" for h in value_res.hints))
    time_range = state.get("time_range") or {}
    if time_range:
        parts.append(f"# 기간\n{time_range.get('start')} ~ {time_range.get('end')}")

    return {
        "schema": "\n\n".join(parts),
        "tables": schema_res.tables,
        "joins": schema_res.joins,
        "value_hints": [h.model_dump() for h in value_res.hints],
        "unresolved": value_res.unresolved,
    }
