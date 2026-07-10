"""generator 노드 — 난이도별 프롬프트·모델로 SQL 을 생성한다.

재생성 루프: validator 실패 시 그 사유(state['validation']['errors'])를 프롬프트에
붙여 다시 생성한다. iteration 을 1 증가시킨다.
(게이트웨이: core.llm / 프롬프트: core.prompts.GENERATOR_SYSTEM, GENERATOR_BY_DIFFICULTY)

입력(state): question, schema, difficulty, model, validation(재시도 시)
출력(state): sql(str), iteration(int)
"""
import re

from app.core import prompts
from app.core.llm import complete
from app.core.settings import settings
from app.graph.state import AgentState

_FENCE = re.compile(r"```(?:sql)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
_START = re.compile(r"(?is)\b(select|with)\b")


def _extract_sql(text: str) -> str:
    """모델 응답에서 SQL 한 문장만 추출 (코드펜스/설명 제거)."""
    m = _FENCE.search(text)
    body = (m.group(1) if m else text).strip()
    m2 = _START.search(body)
    if m2:
        body = body[m2.start():]
    return body.strip().rstrip(";").strip()


def generate(state: AgentState) -> dict:
    iteration = state.get("iteration", 0) + 1
    difficulty = state.get("difficulty", "medium")
    guide_map = prompts.GENERATOR_BY_DIFFICULTY if settings.gen_decompose else prompts.GENERATOR_BY_DIFFICULTY_BASE
    guide = guide_map.get(difficulty, "")

    parts = [f"# 스키마\n{state.get('schema', '')}"]
    fewshot = state.get("fewshot") or []  # [{"question","sql"}] — example_repository 가 채움
    if fewshot:
        parts.append("# 예시 (같은 DB)\n" + "\n".join(
            f"Q: {s['question']}\nSQL: {s['sql']}" for s in fewshot))
    parts.append(f"# 질문\n{state['question']}")
    errors = state.get("validation", {}).get("errors", [])
    if errors:  # 재시도: 직전 검증 오류를 붙여 재생성
        parts.append("# 직전 SQL 의 오류 (수정할 것)\n" + "\n".join(errors))
    user = "\n\n".join(parts)

    res = complete(
        state.get("model", "solar-mini"),
        [
            {"role": "system", "content": f"{prompts.GENERATOR_SYSTEM}\n{guide}"},
            {"role": "user", "content": user},
        ],
        temperature=0.0,
    )
    return {"sql": _extract_sql(res.text), "iteration": iteration}
