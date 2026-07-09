"""LiteLLM 게이트웨이 — 모든 LLM 호출의 단일 진입점.

라우터가 고른 solar 모델로 chat completion 을 호출한다. 토큰/비용/트레이스를
한 곳에서 관리하기 위해, 노드는 직접 litellm 을 부르지 않고 이 함수만 쓴다.

지금은 스켈레톤. **litellm 연결 단계**에서 실제 구현.

입력: model(str, 예 "solar-mini"), messages(list[{"role","content"}]),
      temperature(float|None), max_tokens(int|None)
출력: LLMResult(text, prompt_tokens, completion_tokens, model)
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.settings import settings


@dataclass
class LLMResult:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str = ""


def complete(
    model: str,
    messages: list[dict],
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> LLMResult:
    """LiteLLM 으로 chat completion 1회.

    TODO(litellm 단계): litellm.completion(model=f"upstage/{model}", messages=messages,
        api_key=settings.upstage_api_key, temperature=..., max_tokens=...) 로 교체하고
        response.usage 를 LLMResult 로 매핑.
    """
    raise NotImplementedError("litellm 연결 단계에서 구현")
