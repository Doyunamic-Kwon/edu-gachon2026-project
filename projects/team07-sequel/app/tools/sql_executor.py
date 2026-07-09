"""sql_executor 도구 — 검증된 SQL 을 읽기전용으로 실행한다.

입력: sql(str)
출력: {"columns": list[str], "rows": list[list], "truncated": bool}
제약: SELECT 만, LIMIT(settings.sql_max_rows) 강제, 타임아웃(settings.sql_exec_timeout_s).
엔진: core.db.get_engine() (Supabase read-only)
TODO(tool 단계): read-only 실행 + LIMIT 주입 + statement_timeout 구현.
"""
from __future__ import annotations


def execute_sql(sql: str) -> dict:
    raise NotImplementedError("tool 단계에서 구현")
