"""generator 노드 — 난이도별 프롬프트·모델로 SQL 을 생성한다.

재생성 루프: validator 실패 시 그 사유(state['validation']['errors'])를 프롬프트에
붙여 다시 생성한다. iteration 을 1 증가시킨다.
(게이트웨이: core.llm / 프롬프트: core.prompts.GENERATOR_SYSTEM, GENERATOR_BY_DIFFICULTY)

입력(state): question, schema, difficulty, model, validation(재시도 시)
출력(state): sql(str), iteration(int)
"""
from app.graph.state import AgentState


def generate(state: AgentState) -> dict:
    iteration = state.get("iteration", 0) + 1
    # TODO(litellm 단계): GENERATOR_SYSTEM + GENERATOR_BY_DIFFICULTY[difficulty] 프롬프트로
    #                    llm.complete(model=state["model"], messages=...) 호출
    return {"sql": "SELECT 1", "iteration": iteration}
