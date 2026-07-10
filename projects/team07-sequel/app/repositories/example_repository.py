"""example_repository — few-shot 예시(질문→SQL) 풀 접근.

파인튜닝 대신 in-context few-shot 을 위한 과거 (질문, SQL) 예시 저장/검색.
(벤치마크 결과: few-shot 이 정확도의 핵심 레버 — schema+few 조건 최고)

입력: question(str), k(int)
출력: [{"question": str, "sql": str}, ...]  유사 예시 top-k
소스: 예시 저장소 (추후 결정: DB 테이블 / 벡터스토어)
TODO(tool 단계): 유사도 검색(문자열/임베딩) 구현.
"""
from __future__ import annotations


def retrieve_examples(question: str, k: int = 3) -> list[dict]:
    raise NotImplementedError("tool 단계에서 구현")
