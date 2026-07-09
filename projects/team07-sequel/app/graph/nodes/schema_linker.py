"""schema_linker 노드 — 자연어 질의에서 관련 스키마만 추린다.

의도·대상 테이블·조건을 파악해 전체 카탈로그에서 관련 테이블/컬럼만 남기고,
셀 값 매칭으로 값 예시를 붙인다.
(도구: tools.schema_retriever, tools.value_retriever / 데이터: repositories)

입력(state): question
출력(state): schema(str, 링크된 DDL + 컬럼 샘플 값), tables(list[str])
"""
from app.graph.state import AgentState


def schema_link(state: AgentState) -> dict:
    _question = state["question"]
    # TODO(tool 단계): schema_retriever(question) 로 관련 테이블/DDL,
    #                 value_retriever(question, tables) 로 값 예시 결합
    return {"schema": "", "tables": []}
