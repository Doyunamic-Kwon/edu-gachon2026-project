"""schema_repository — DB 스키마 카탈로그(테이블·컬럼·DDL) 접근.

입력: (없음) / tables(list[str])
출력: 테이블 목록 / 테이블별 컬럼·타입·DDL 문자열
소스: core.db (information_schema) 또는 캐시된 카탈로그
TODO(tool 단계): information_schema 조회로 카탈로그 로드.
"""
from __future__ import annotations


def list_tables() -> list[str]:
    raise NotImplementedError("tool 단계에서 구현")


def get_ddl(tables: list[str]) -> str:
    raise NotImplementedError("tool 단계에서 구현")
