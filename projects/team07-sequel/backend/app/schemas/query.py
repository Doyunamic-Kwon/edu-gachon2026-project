from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """프론트엔드 -> 백엔드 요청 스펙."""

    # max_length=2000: agent(docs/api.md) 쪽 제약과 동일하게 맞춤.
    # 안 맞추면 여기서는 통과됐다가 agent에서 422로 튕겨나가 에러 처리가 애매해짐.
    question: str = Field(..., min_length=1, max_length=2000, description="사용자의 자연어 질문")
    session_id: str = Field(..., description="대화 세션 식별자 (프론트에서 생성/유지)")


class AgentResult(BaseModel):
    """백엔드 -> AI agent 호출 결과 (agent_client.py의 반환 타입).

    실제 AI agent의 응답 형태가 무엇이든, agent_client.py 안에서 이 형태로
    변환해서 반환하면 나머지 코드는 전혀 바뀌지 않는다.
    """

    sql: str
    summary: str
