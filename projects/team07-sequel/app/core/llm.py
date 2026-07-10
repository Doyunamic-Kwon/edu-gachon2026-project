"""LiteLLM 게이트웨이 — 모든 LLM 호출의 단일 진입점.

라우터가 고른 solar 모델로 chat completion 을 호출한다. 노드는 직접 litellm 을
부르지 않고 이 함수만 쓴다(토큰/비용/트레이스 단일화).

Upstage 는 OpenAI 호환이라 litellm 의 openai provider + api_base 로 호출한다
(solar-pro3 등 임의 모델 문자열도 그대로 통과).

입력: model(str, 예 "solar-mini"), messages(list[{"role","content"}]),
      temperature(float|None), max_tokens(int|None)
출력: LLMResult(text, prompt_tokens, completion_tokens, model)
"""
from __future__ import annotations

import threading
from dataclasses import dataclass

import litellm

from app.core.settings import settings

litellm.suppress_debug_info = True

# 직전 complete() 호출의 토큰 사용량 (스레드별) — 비용 계측용(예: route_eval).
_last = threading.local()


def last_usage() -> tuple[int, int]:
    """이 스레드에서 마지막 complete() 의 (prompt_tokens, completion_tokens)."""
    return getattr(_last, "usage", (0, 0))


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
    """Solar chat completion 1회 (Upstage OpenAI 호환)."""
    resp = litellm.completion(
        model=f"openai/{model}",
        messages=messages,
        api_base=settings.upstage_base_url,
        api_key=settings.upstage_api_key,
        temperature=settings.llm_temperature if temperature is None else temperature,
        max_tokens=settings.llm_max_tokens if max_tokens is None else max_tokens,
        num_retries=3,   # 레이트리밋/일시오류 지수 백오프 재시도 (Retry-After 준수)
        timeout=60,
    )
    usage = resp.usage
    ptok = getattr(usage, "prompt_tokens", 0)
    ctok = getattr(usage, "completion_tokens", 0)
    _last.usage = (ptok, ctok)
    return LLMResult(
        text=resp.choices[0].message.content or "",
        prompt_tokens=ptok,
        completion_tokens=ctok,
        model=model,
    )
