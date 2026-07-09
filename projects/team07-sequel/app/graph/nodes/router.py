"""router 노드 — 난이도(하/중/상/최상) 분류 + solar 모델 선택 + injection 가드레일.

LiteLLM 으로 질의 난이도를 4분류하고 settings.model_by_difficulty 로 모델을 정한다.
동시에 프롬프트 인젝션/위험 요청을 사전 판정한다.
(게이트웨이: core.llm / 프롬프트: core.prompts.ROUTER_CLASSIFY, INJECTION_GUARD)

입력(state): question, schema
출력(state): difficulty(str), model(str), safety({"ok": bool, "reason": str})
"""
from app.core.settings import settings
from app.graph.state import AgentState, Difficulty


def route(state: AgentState) -> dict:
    # TODO(litellm 단계): LLM 난이도 분류 + injection 판정으로 교체
    difficulty = Difficulty.MEDIUM.value
    return {
        "difficulty": difficulty,
        "model": settings.model_by_difficulty[difficulty],
        "safety": {"ok": True, "reason": ""},
    }
