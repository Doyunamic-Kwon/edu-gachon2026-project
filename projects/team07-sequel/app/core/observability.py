"""Langfuse 관측 — 트레이싱·비용/품질 로깅의 단일 지점.

노드/LLM 호출을 트레이스로 남긴다. 지금은 스켈레톤.

TODO(langfuse 단계): langfuse client 초기화 + trace/span 헬퍼 구현.
"""
from __future__ import annotations

from contextlib import contextmanager

from app.core.settings import settings


def init_observability() -> None:
    """앱 시작 시 Langfuse 초기화. 키 없으면 no-op.

    입력: settings.langfuse_* 키
    출력: None
    TODO(langfuse 단계): Langfuse(public_key=..., secret_key=..., host=...) 생성.
    """
    return None


@contextmanager
def trace(name: str, **meta):
    """노드/LLM 실행을 감싸는 트레이스 컨텍스트 (지금은 no-op).

    입력: name(span 이름), meta(부가 속성)
    출력: span 핸들 (지금은 None)
    TODO(langfuse 단계): span 생성/종료로 교체.
    """
    yield None
