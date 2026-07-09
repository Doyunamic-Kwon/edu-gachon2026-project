"""formatter 노드 — 실행 결과를 표 + 자연어 요약으로 만든다.

결론 먼저(숫자·근거 명시), 필요 시 SQL 원문 공개. 검증/실행 실패·안전성 거절 시
명확한 안내 메시지를 만든다.
(게이트웨이: core.llm / 프롬프트: core.prompts.SUMMARY)

입력(state): question, result, sql, validation, safety, error
출력(state): answer({"summary", "table", "sql", "disclaimer"})
"""
from app.graph.state import AgentState, empty_answer


def format_answer(state: AgentState) -> dict:
    result = state.get("result", {})
    # TODO(litellm 단계): SUMMARY 프롬프트 + llm.complete 로 결과 기반 자연어 요약 생성.
    #                    안전성 거절/오류 상태면 고정 안내 메시지로 분기.
    return {
        "answer": empty_answer(
            table={"columns": result.get("columns", []), "rows": result.get("rows", [])},
            sql=state.get("sql", ""),
        )
    }
