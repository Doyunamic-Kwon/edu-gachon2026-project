"""schema_retriever 도구 — 질의와 관련된 테이블/컬럼을 카탈로그에서 검색한다.

입력: question(str)
출력: {"tables": list[str], "ddl": str}  관련 테이블 이름 + 해당 DDL
데이터: repositories.schema_repository
TODO(tool 단계): 문자열/임베딩 기반 관련 테이블 랭킹 구현.
"""
from __future__ import annotations


def retrieve_schema(question: str) -> dict:
    raise NotImplementedError("tool 단계에서 구현")
