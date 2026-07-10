"""스키마/값 링커 회귀 평가 — 라벨셋으로 recall@k · 값 정확도 · 마진 확인.

임계(settings.link_*/value_*)·데이터·임베딩 모델이 바뀌면 재실행해 회귀 감지.
이 라벨셋이 회귀 테스트셋이다. 실 Supabase + 임베딩 호출 필요.

실행:  uv run python -m tests.eval_linker
"""
from __future__ import annotations

from app.tools.schema_retriever import retrieve_schema
from app.tools.value_retriever import retrieve_values

# 질문 → 반드시 검색돼야 할 gold 테이블(부분집합). recall 관점(빠지면 SQL 불가).
SCHEMA_LABELS = {
    "해지한 고객 수": {"telco_customer_churn"},
    "가장 많이 팔린 상품 카테고리": {"olist_products", "olist_order_items"},
    "주문별 결제 금액": {"olist_order_payments"},
    "지역별 고객 분포": {"olist_customers"},
}

# (키워드, 테이블, gold 값) — synonym/embedding 경로 모두 커버
VALUE_LABELS = [
    ("취소", "olist_orders", "canceled"),          # synonym
    ("배송 완료", "olist_orders", "delivered"),     # synonym
    ("해지", "olist_orders", "canceled"),           # synonym
    ("신용카드", "olist_order_payments", "credit_card"),  # embedding (사전에 없음)
]


def eval_schema() -> bool:
    print("== schema recall@k ==")
    hit = 0
    for q, gold in SCHEMA_LABELS.items():
        tables = set(retrieve_schema(q).tables)
        ok = gold <= tables
        hit += ok
        print(f"  [{'O' if ok else 'X'}] {q}  (retrieved {len(tables)}개)  missing={sorted(gold - tables)}")
    print(f"  recall: {hit}/{len(SCHEMA_LABELS)}\n")
    return hit == len(SCHEMA_LABELS)


def eval_value() -> bool:
    print("== value accuracy ==")
    hit = 0
    for kw, table, gold in VALUE_LABELS:
        res = retrieve_values([kw], [table])
        h = res.hints[0] if res.hints else None
        val = h.value if h else None
        ok = val == gold
        hit += ok
        info = (f"how={h.how} score={h.score} candidates={h.candidates}"
                if h else f"not_found (unresolved={res.unresolved})")
        print(f"  [{'O' if ok else 'X'}] {kw} -> {gold} | got={val} | {info}")
    print(f"  accuracy: {hit}/{len(VALUE_LABELS)}")
    return hit == len(VALUE_LABELS)


if __name__ == "__main__":
    ok_schema = eval_schema()
    ok_value = eval_value()
    if not (ok_schema and ok_value):  # 회귀 감지: CI/자동화에서 실패로 종료
        raise SystemExit(1)
