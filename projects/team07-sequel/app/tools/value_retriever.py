"""value_retriever 도구 — 질의 리터럴을 실제 셀 값과 매칭한다 (어느 컬럼에 있는지).

입력: question(str), tables(list[str])
출력: {"hints": list[str]}  "값 'X' 는 T.C 컬럼에 존재" 형태 힌트
데이터: repositories.value_repository
TODO(tool 단계): exact/ILIKE 문자열 매칭(+선택적 임베딩) 구현.
"""
from __future__ import annotations


def retrieve_values(question: str, tables: list[str]) -> dict:
    raise NotImplementedError("tool 단계에서 구현")
