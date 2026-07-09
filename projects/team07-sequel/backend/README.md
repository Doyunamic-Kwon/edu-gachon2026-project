# Text2SQL Backend

FastAPI 기반 백엔드. 프론트엔드로부터 자연어 질문을 받아, (지금은 mock인) AI agent에게
SQL 생성을 요청하고, 안전성 검증을 거쳐 Supabase(Postgres)에서 조회한 결과를
SSE(Server-Sent Events)로 실시간 스트리밍한다.

## 폴더 구조

```
Backend/
├── app/
│   ├── main.py                  # FastAPI 앱 생성, CORS, 라우터 등록
│   ├── api/routes/query.py      # POST /api/query — 유일한 진입점, SSE 스트리밍 처리
│   ├── schemas/query.py         # 요청/응답 Pydantic 모델, SSE 이벤트·에러코드 상수
│   ├── services/
│   │   ├── agent_client.py      # AI agent 호출 어댑터 (현재 mock, 나중에 실제 HTTP 호출로 교체)
│   │   ├── session_store.py     # 세션별 대화 히스토리 (후속 질문 지원, 인메모리)
│   │   └── guardrail.py         # SQL 안전성 2차 검증 (SELECT만 허용, LIMIT 강제)
│   ├── db/database.py           # Supabase(Postgres) 연결 및 조회 실행
│   └── core/config.py           # 환경변수 로드
├── requirements.txt
└── Dockerfile
```

## 요청/응답 스펙

**요청**

```
POST /api/query
Content-Type: application/json

{ "question": "카테고리별 주문 수 알려줘", "session_id": "abc-123" }
```

**응답 (SSE, `text/event-stream`) — teammate(권도윤) agent의 포맷(`docs/api.md`)에 맞춤**

표준 SSE의 `event:` 줄은 쓰지 않는다. 매 청크가 `data: <JSON>\n\n` 한 줄뿐이고,
그 JSON 안의 `"event"` 키로 종류를 구분한다.

| event | 필드 | 의미 |
|---|---|---|
| `node` | `node`(노드명), `data`(그 노드 결과, JSON 문자열) | 진행 상황. 노드: `generate`(SQL 생성) → `validate`(가드레일 검증) → `execute`(DB 실행) |
| `done` | `data`(최종 answer, JSON 문자열: `{summary, table:{columns,rows}, sql, disclaimer}`) | 정상 종료 |
| `error` | `data`(사유 문자열) | 실패. 어느 단계에서든 발생 가능, 발생 즉시 스트림 종료 |

```text
data: {"event":"node","node":"generate","data":"{\"sql\":\"SELECT ...\"}"}

data: {"event":"node","node":"validate","data":"{\"validation\":{\"ok\":true,\"errors\":[]}}"}

data: {"event":"node","node":"execute","data":"{\"result\":{\"columns\":[...],\"rows\":[...],\"truncated\":false}}"}

data: {"event":"done","data":"{\"summary\":\"...\",\"table\":{\"columns\":[...],\"rows\":[...]},\"sql\":\"...\",\"disclaimer\":\"\"}"}
```

## 로컬 실행

### 1) 환경변수

`Backend/.env` 파일에 아래 값이 필요하다 (커밋하지 않음, 팀원과 직접 공유).

```dotenv
SUPABASE_DB_URL=postgresql://text2sql_reader.<project-ref>:<비밀번호>@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres
PORT=8080
```

### 2) uvicorn으로 직접 실행

```bash
pip install -r requirements.txt
export SUPABASE_DB_URL="..."
uvicorn app.main:app --reload --port 8080
```

### 3) Docker로 실행 (Cloud Run 환경에 더 가깝게 검증)

```bash
docker build -t text2sql-backend .
docker run -p 8080:8080 --env-file .env text2sql-backend
```

확인:

```bash
curl http://localhost:8080/healthz
# {"status":"ok"}
```

## 현재 상태 / TODO

- **AI agent 연동 (`services/agent_client.py`)**: teammate(권도윤)의 `aiagent` 브랜치
  `docs/api.md` 스펙에 맞춰 실제 HTTP 연동 완료 (`POST {AI_AGENT_BASE_URL}/api/v1/query`).
  로컬에서 테스트하려면 agent 서버가 `http://localhost:8000`(또는
  `AI_AGENT_BASE_URL` 환경변수로 지정한 주소)에서 먼저 떠 있어야 한다.
  agent가 아직 스켈레톤 상태라 `sql: "SELECT 1"` 같은 placeholder가 돌아올 수 있음.
  agent 응답에 이미 실행된 rows/columns가 있지만 사용하지 않고, `sql` 문자열만
  가져와 우리 쪽 guardrail로 재검증 후 우리 자체 읽기 전용 계정으로 재실행한다.
- **세션/히스토리**: agent 스펙에 `session_id`/history 필드가 없어서, 후속 질문 맥락은
  아직 우리 backend 안에만 쌓이고 agent에는 전달되지 않는다. agent가 지원하게 되면
  `agent_client.py`에서 함께 넘기면 된다.
- **재생성 피드백 루프**: SQL 검증 실패 시 AI agent에게 사유를 돌려주고 재시도시키는 로직은
  아직 없음 (지금은 실패하면 바로 `error` 이벤트로 종료).
- **결과 검증(행 수/스키마/타입 재확인)**: 아직 없음. 현재는 결과가 비어있는지만 확인.
- **CORS**: 지금은 전체 허용(`*`). 배포 시 프론트엔드 실제 URL로 제한 필요.
- **CI/CD (`.github/workflows/*.yml`)**: 아직 작성 전.
- **폴더 위치**: 지금은 저장소 루트의 `backend/`에 있음. teammate의 `projects/team07-sequel/`
  구조로 옮길지는 팀원과 상의 후 결정 예정 (해당 폴더에 우리 프로젝트와 무관한 파일이
  섞여 있어 확인 필요).

## 안전장치 (guardrail.py)

AI agent가 생성한 SQL을 그대로 실행하지 않고, 실행 전에 아래를 검사한다.

- `SELECT`로 시작하지 않으면 차단
- `INSERT`/`UPDATE`/`DELETE`/`DROP`/`ALTER`/`TRUNCATE`/`CREATE`/`GRANT`/`REVOKE` 포함 시 차단
- `LIMIT`이 없으면 기본값(`LIMIT 200`)을 자동으로 붙임

DB 연결 자체도 읽기 전용 계정(`text2sql_reader`)이라 쓰기 쿼리는 DB 레벨에서도 이중으로 막힌다.
