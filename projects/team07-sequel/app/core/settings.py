"""애플리케이션 설정 — 단일 소스(single source of truth).

`.env` 를 자동 로드하는 타입 있는 Settings. 모든 모듈은
`from app.core.settings import settings` 로 **여기서만** 설정을 읽는다
(os.getenv 를 코드 곳곳에 흩뿌리지 않는다).

입력: 환경변수 / .env
출력: `settings` 싱글턴 인스턴스
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
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
    # 확정 파이프라인 라우팅 그리드(n=400, mini/pro2/pro3 × k0/k3/k8, 공식 EX)로 재검증 후 확정.
    # 하·상: mini|k3 가 pro2|k3 대비 -2pp 로 정답당 비용도 더 싸고 총비용 -12~19%(k0→k3 는
    # 실패율↓ 몫이 커서 정답당 비용도 낮아짐 — "토큰 아끼려 few-shot 줄이면 실패율로 더 손해").
    # 중: mini 는 k3=-12pp(정확도 붕괴)·k8=+20%(비용 역전)라 대안이 없어 pro2 유지.
    # 최상: pro2|k8 이 KPI(70%) 74% 달성(마진 확보) — mini|k8(73%,-11%비용)은 마진이 얇아 보류.
    # 근거: docs/실험_총정리.md §7-4.
    model_easy: str = "solar-mini"
    model_medium: str = "solar-pro2"
    model_hard: str = "solar-mini"
    model_extra_hard: str = "solar-pro2"
    # 난이도별 라우팅 확정 → 강제 오버라이드 해제("" = model_by_difficulty 사용).
    route_force_model: str = ""

    # ── 실행 가드레일 ──
    sql_max_rows: int = 1000
    sql_exec_timeout_s: float = 5.0
    agent_max_retries: int = 2

    # ── 스키마/값 링킹 튜닝 ──
    # 상수 박지 말고 여기서. score 분포를 Langfuse 로 로깅해 재캘리브레이션,
    # 회귀 측정은 tests/eval_linker.py (recall@k · 마진 분포).
    link_table_min_k: int = 3        # recall 우선: 최소 이만큼은 확보
    link_table_max_k: int = 8
    # BIRD ablation: 스키마가 작으면 임베딩 축소가 오히려 recall 손실(-2.9pp) → 전체 스키마 사용
    link_full_schema_max: int = 20   # 총 테이블 <= 이 값이면 retriever 스킵(전체 DDL)
    link_elbow_gap: float = 0.03     # 인접 점수 gap 이 크면 컷(적응적 k)
    link_enum_max_card: int = 10     # 유니크 <= 이 값이면 enum → 마진 없이 top-1
    value_cat_limit: int = 60        # distinct <= 이 값이면 categorical 로 캐시
    value_max_values: int = 300      # 임베딩 후보 상한
    value_fuzzy_min: int = 85
    value_emb_floor: float = 0.40    # 이보다 낮으면 no-match (정답 없음 방어)
    value_emb_margin: float = 0.05   # free-text top1-top2; 미달이면 버리지 말고 ambiguous
    # 키워드가 셀 값보다 컬럼명에 더 가까우면(+margin) 스키마 개념으로 보고 값 매칭 스킵
    # ("발행 연도" 같은 컬럼 개념이 임의 셀 값에 억지 매칭되던 실링커 노이즈 방어)
    value_colname_margin: float = 0.0

    # ── LLM (LiteLLM / Upstage) ──
    upstage_api_key: str = ""
    upstage_base_url: str = "https://api.upstage.ai/v1"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 800
    # BIRD leave-one-out: CTE 분해 가이드 제거 시 +0.6pp(무효~미세 해악) → 기본 off
    gen_decompose: bool = False  # hard/extra_hard 에 단계분해·CTE 가이드
    # 라우팅 그리드(n=400)로 난이도별 확정: 최상만 k8(+6pp, KPI 70% 달성의 핵심), 나머지는 k3
    # (k8 은 프롬프트가 커져 중·하·상에선 이득 대비 비용이 안 맞음 — §7-4). few-shot 자체는
    # 전 난이도 필수(하에서도 k0→k3 +25~31pp).
    fewshot_k_easy: int = 3
    fewshot_k_medium: int = 3
    fewshot_k_hard: int = 3
    fewshot_k_extra_hard: int = 8

    # ── Langfuse (트레이싱·비용/품질 로깅) ──
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    # LANGFUSE_HOST / LANGFUSE_BASE_URL 둘 다 허용 (.env·서버 시크릿이 BASE_URL 명명 —
    # 미스매치 시 기본 EU 호스트로 전송돼 JP 프로젝트에 트레이스가 안 뜨는 사고 방지)
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com",
        validation_alias=AliasChoices("LANGFUSE_HOST", "LANGFUSE_BASE_URL"),
    )

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

    @property
    def fewshot_k_by_difficulty(self) -> dict[str, int]:
        """Difficulty 값 → few-shot 예시 개수. generator 가 슬라이싱에 사용."""
        return {
            "easy": self.fewshot_k_easy,
            "medium": self.fewshot_k_medium,
            "hard": self.fewshot_k_hard,
            "extra_hard": self.fewshot_k_extra_hard,
        }

    @property
    def fewshot_k_max(self) -> int:
        """schema_link 가 route 이전에 미리 확보해 둘 개수(난이도별 최댓값).

        route(난이도 확정)가 schema_link 뒤에 오므로, 링킹 시점엔 실제 필요한 k 를
        모른다 — 최댓값만큼 검색해 두고 generator 가 difficulty 로 잘라 쓴다.
        """
        return max(self.fewshot_k_by_difficulty.values())


@lru_cache
def get_settings() -> Settings:
    """설정 싱글턴 (테스트에서 override 가능하도록 함수로 감쌈)."""
    return Settings()


settings = get_settings()
