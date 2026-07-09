"""에이전트 그래프의 공유 상태.

`AgentState` 는 LangGraph 노드들이 함께 읽고 쓰는 단일 상태 딕셔너리다.
각 노드는 필요한 키를 읽고, 자기가 새로 만든 키만 부분 dict 로 반환한다
(LangGraph 가 기존 상태에 병합).

파이프라인 순서대로 키가 채워진다:
    question → (schema_link) schema/tables → (route) difficulty/model/safety
    → (generate) sql → (validate) validation → (execute) result → (format) answer
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from typing_extensions import TypedDict


class Difficulty(str, Enum):
    """질의 난이도 4단계 (AI Hub hardness 와 정렬: 하/중/상/최상)."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXTRA_HARD = "extra_hard"


class AgentState(TypedDict, total=False):
    # ── 입력 ──
    question: str                 # 사용자 자연어 질의

    # ── schema_linker 산출 ──
    schema: str                   # 링크된 관련 스키마 (DDL + 컬럼 샘플 값)
    tables: list[str]             # 관련 테이블 이름 목록

    # ── router 산출 ──
    difficulty: str               # Difficulty 값
    model: str                    # 선택된 solar 모델 문자열
    safety: dict                  # injection 가드레일 {"ok": bool, "reason": str}

    # ── generator 산출 ──
    sql: str                      # 생성된 SQL (SELECT)

    # ── validator 산출 ──
    validation: dict              # {"ok": bool, "errors": list[str]}

    # ── executor 산출 ──
    result: dict                  # {"columns": [...], "rows": [...], "format": str, "truncated": bool}

    # ── formatter 산출 ──
    answer: dict                  # {"summary": str, "table": {...}, "sql": str, "disclaimer": str}

    # ── 제어 ──
    iteration: int                # 재생성 루프 카운터 (validate 실패 시 generate 로 되돌림)
    error: str                    # 파이프라인 오류 메시지 (있으면 formatter 가 안내)


def initial_state(question: str) -> AgentState:
    """사용자 질의로부터 그래프 초기 상태를 만든다.

    입력: question(str)
    출력: AgentState (question, iteration=0 만 채운 초기값)
    """
    return {"question": question, "iteration": 0}


def empty_answer(**over: Any) -> dict:
    """answer 기본 골격. over 로 일부 필드 덮어쓰기."""
    base = {"summary": "", "table": {"columns": [], "rows": []}, "sql": "", "disclaimer": ""}
    base.update(over)
    return base
