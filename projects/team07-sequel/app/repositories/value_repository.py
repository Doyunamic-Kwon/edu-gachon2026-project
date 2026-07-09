"""value_repository — 컬럼 값 조회(셀 매칭용 distinct 값·리터럴 검색).

입력: table, column, k / literal
출력: distinct 값 예시 / literal 이 존재하는 (table, column) 목록
소스: core.db (읽기 전용)
TODO(tool 단계): SELECT DISTINCT … LIMIT k / ILIKE 검색 구현.
"""
from __future__ import annotations


def sample_values(table: str, column: str, k: int = 3) -> list:
    raise NotImplementedError("tool 단계에서 구현")


def find_columns_with_value(literal: str) -> list[tuple[str, str]]:
    raise NotImplementedError("tool 단계에서 구현")
