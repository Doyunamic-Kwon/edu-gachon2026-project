import os


class Settings:
    """환경변수 로드. 실제 값은 .env 파일(팀원과 공유 중)에서 채워짐."""

    SUPABASE_DB_URL: str = os.environ.get("SUPABASE_DB_URL", "")
    PORT: int = int(os.environ.get("PORT", "8080"))

    # AI agent(teammate의 aiagent 브랜치, docs/api.md 기준) 서비스 주소.
    # 로컬에서 agent를 직접 띄웠을 때의 기본 포트로 맞춰둠. 배포 시에는
    # 실제 Cloud Run URL로 교체.
    AI_AGENT_BASE_URL: str = os.environ.get("AI_AGENT_BASE_URL", "http://localhost:8000")


settings = Settings()
