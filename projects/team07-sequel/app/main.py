"""FastAPI 진입점 — Sequel Text-to-SQL 에이전트 API."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.observability import init_observability
from app.core.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_observability()  # Langfuse (langfuse 연결 단계에서 실제 초기화)
    yield


app = FastAPI(title="Sequel — Text-to-SQL Agent", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api/v1", tags=["query"])


@app.get("/health")
def health():
    return {"status": "healthy"}
