"""sql_validator 도구 — sqlglot 로 SQL 을 검증한다.

입력: sql(str), schema(str, 허용 테이블/컬럼)
출력: {"ok": bool, "errors": list[str]}
검사: 파싱 가능, SELECT 만, 금지 키워드/DDL·DML 차단, 화이트리스트 밖 테이블/컬럼 거부.
TODO(tool 단계): sqlglot.parse_one(sql, dialect="postgres") 기반 검증 구현.
"""
from __future__ import annotations


def validate_sql(sql: str, schema: str) -> dict:
    raise NotImplementedError("tool 단계에서 구현")
