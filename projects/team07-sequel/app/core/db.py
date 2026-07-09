"""대상 데이터베이스 접근 — Supabase(PostgreSQL) 읽기 전용 엔진.

executor(및 repositories)가 여기서 커넥션을 얻는다. 안전성은 DB 측
read-only 계정(text2sql_reader)으로 1차 보장하고, 앱 측에서 SELECT-only 를 재확인한다.

지금은 스켈레톤.

입력: settings.sqlalchemy_url (Supabase Session Pooler, psycopg3 드라이버)
출력: SQLAlchemy Engine
TODO(tool 단계): create_engine(settings.sqlalchemy_url, pool_pre_ping=True) 생성.
"""
from __future__ import annotations

from app.core.settings import settings

_engine = None


def get_engine():
    """읽기 전용 DB 엔진을 반환한다 (지연 생성·싱글턴).

    TODO(tool 단계): SQLAlchemy create_engine(settings.sqlalchemy_url).
    Supabase 는 반드시 Pooler 주소 사용(Direct 는 IPv6 전용).
    """
    raise NotImplementedError("tool 단계에서 구현 (Supabase read-only 엔진)")
