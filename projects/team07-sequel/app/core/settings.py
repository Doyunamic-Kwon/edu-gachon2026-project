"""애플리케이션 설정 — 단일 소스(single source of truth).

`.env` 를 자동 로드하는 타입 있는 Settings. 모든 모듈은
`from app.core.settings import settings` 로 **여기서만** 설정을 읽는다
(os.getenv 를 코드 곳곳에 흩뿌리지 않는다).

입력: 환경변수 / .env
출력: `settings` 싱글턴 인스턴스
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=(),  # MODEL_* 필드명 허용 (pydantic 보호 네임스페이스 해제)
    )

    # ── 앱 / CORS ──
    cors_origins: list[str] = ["http://localhost:5173"]  # React dev 기본

    # ── 대상 DB: Supabase(PostgreSQL), 읽기 전용 계정(text2sql_reader) + Session Pooler ──
    # .env 의 SUPABASE_DB_URL 로 덮어씀. 로컬 기본은 dev postgres.
    supabase_db_url: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    db_schema: str = "public"  # 화이트리스트 대상 스키마

    # ── 난이도별 solar 모델 라우팅 ──
    # route_eval n=300(few-shot, 우리 generator)로 확정한 비용인지 라우팅.
    # 하·중은 mini 로 충분(81/78%), 상·최상은 pro2 정확도 우위(79/60%). pro3 제외
    # (모든 난이도 pro2 이하, 동일 단가). 근거: docs/difficulty_criteria.md.
    model_easy: str = "solar-mini"
    model_medium: str = "solar-mini"
    model_hard: str = "solar-pro2"
    model_extra_hard: str = "solar-pro2"
    # 런칭 안정화: 값 비었을 때만 위 난이도 라우팅 적용. 지금은 전부 pro2 고정
    # (router 는 분류를 계속 하되 model 만 이 값으로 덮음). ""로 두면 검증된 라우팅 복귀.
    route_force_model: str = "solar-pro2"

    # ── 실행 가드레일 ──
    sql_max_rows: int = 1000
    sql_exec_timeout_s: float = 5.0
    agent_max_retries: int = 2

    # ── 스키마/값 링킹 튜닝 ──
    # 상수 박지 말고 여기서. score 분포를 Langfuse 로 로깅해 재캘리브레이션,
    # 회귀 측정은 tests/eval_linker.py (recall@k · 마진 분포).
    link_table_min_k: int = 3        # recall 우선: 최소 이만큼은 확보
    link_table_max_k: int = 8
    link_elbow_gap: float = 0.03     # 인접 점수 gap 이 크면 컷(적응적 k)
    link_enum_max_card: int = 10     # 유니크 <= 이 값이면 enum → 마진 없이 top-1
    value_cat_limit: int = 60        # distinct <= 이 값이면 categorical 로 캐시
    value_max_values: int = 300      # 임베딩 후보 상한
    value_fuzzy_min: int = 85
    value_emb_floor: float = 0.40    # 이보다 낮으면 no-match (정답 없음 방어)
    value_emb_margin: float = 0.05   # free-text top1-top2; 미달이면 버리지 말고 ambiguous

    # ── LLM (LiteLLM / Upstage) ──
    upstage_api_key: str = ""
    upstage_base_url: str = "https://api.upstage.ai/v1"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 800
    gen_decompose: bool = True  # hard/extra_hard 에 단계분해·CTE 가이드 (off=기본 프롬프트)

    # ── Langfuse (트레이싱·비용/품질 로깅) ──
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, v):
        """CORS_ORIGINS 를 콤마 구분 문자열로도 받도록 허용."""
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def sqlalchemy_url(self) -> str:
        """SQLAlchemy 용 URL — psycopg3 드라이버 명시.

        Supabase 문자열(postgresql://…)을 postgresql+psycopg://… 로 변환.
        """
        url = self.supabase_db_url
        if url.startswith("postgresql://"):
            return "postgresql+psycopg://" + url[len("postgresql://"):]
        return url

    @property
    def model_by_difficulty(self) -> dict[str, str]:
        """Difficulty 값 → solar 모델 문자열."""
        return {
            "easy": self.model_easy,
            "medium": self.model_medium,
            "hard": self.model_hard,
            "extra_hard": self.model_extra_hard,
        }


@lru_cache
def get_settings() -> Settings:
    """설정 싱글턴 (테스트에서 override 가능하도록 함수로 감쌈)."""
    return Settings()


settings = get_settings()
