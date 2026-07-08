"""
Text2SQL 프로젝트 - Supabase(Postgres)에 Olist/Telco Churn/Support Ticket 데이터 적재 스크립트

사용법:
    export DATABASE_URL="postgresql://postgres:<비밀번호>@db.<프로젝트-ref>.supabase.co:5432/postgres"
    pip install pandas sqlalchemy psycopg2-binary --break-system-packages   # (필요시)
    python load_data.py

주의:
    - DATABASE_URL은 admin(postgres) 계정 문자열입니다. 이 스크립트는 데이터 적재 용도로만 admin 계정을 쓰고,
      끝나면 별도의 읽기 전용(text2sql_reader) 계정을 만들어 백엔드는 그쪽을 쓰게 됩니다.
    - 비밀번호에 @, /, : 같은 특수문자가 있으면 URL 인코딩이 필요합니다.
"""

import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

BASE_DIR = Path(__file__).parent / "csv_dataset"
OLIST_DIR = BASE_DIR / "Brazilian_E-Commerce_Public_Dataset_by_Olist"

# (CSV 파일 경로, 생성할 테이블명)
FILES = [
    (OLIST_DIR / "olist_customers_dataset.csv", "olist_customers"),
    (OLIST_DIR / "olist_geolocation_dataset.csv", "olist_geolocation"),
    (OLIST_DIR / "olist_sellers_dataset.csv", "olist_sellers"),
    (OLIST_DIR / "olist_products_dataset.csv", "olist_products"),
    (OLIST_DIR / "product_category_name_translation.csv", "olist_product_category_translation"),
    (OLIST_DIR / "olist_orders_dataset.csv", "olist_orders"),
    (OLIST_DIR / "olist_order_items_dataset.csv", "olist_order_items"),
    (OLIST_DIR / "olist_order_payments_dataset.csv", "olist_order_payments"),
    (OLIST_DIR / "olist_order_reviews_dataset.csv", "olist_order_reviews"),
    (BASE_DIR / "Telco_Customer_Churn.csv", "telco_customer_churn"),
    (BASE_DIR / "customer_support_tickets.csv", "customer_support_tickets"),
]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """컬럼명을 Postgres에서 다루기 쉬운 snake_case로 정리."""
    df.columns = (
        df.columns.str.strip()
        .str.replace(r"[^0-9a-zA-Z]+", "_", regex=True)
        .str.strip("_")
        .str.lower()
    )
    return df


def main() -> None:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL 환경변수가 설정되어 있지 않습니다.")
        print('  export DATABASE_URL="postgresql://postgres:<비밀번호>@db.<ref>.supabase.co:5432/postgres"')
        sys.exit(1)

    engine = create_engine(db_url)

    for csv_path, table_name in FILES:
        if not csv_path.exists():
            print(f"[SKIP] 파일 없음: {csv_path}")
            continue

        print(f"[LOAD] {csv_path.name} -> {table_name}")
        # geolocation처럼 큰 파일 대비 chunksize로 나눠서 적재
        chunk_iter = pd.read_csv(csv_path, chunksize=20000, low_memory=False)
        first_chunk = True
        total_rows = 0
        for chunk in chunk_iter:
            chunk = normalize_columns(chunk)
            chunk.to_sql(
                table_name,
                engine,
                if_exists="replace" if first_chunk else "append",
                index=False,
                method="multi",
                chunksize=5000,
            )
            first_chunk = False
            total_rows += len(chunk)
        print(f"       완료: {total_rows}행 적재됨")

    print("\n전체 데이터 적재 완료.")


if __name__ == "__main__":
    main()
