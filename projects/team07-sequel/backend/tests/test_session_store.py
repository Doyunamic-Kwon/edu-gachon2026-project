"""session_store 테스트.

세션별 대화 히스토리가 정확히 쌓이고, 오래된 턴이 잘 잘려나가고, 서로 다른
세션끼리 섞이지 않는지 확인한다. 지금은 인메모리 딕셔너리 구현이라 모듈
전역 상태(_sessions)를 공유하므로, 테스트 간 상태가 새는 것을 막기 위해
매 테스트 전에 초기화하는 fixture를 둔다.
"""

import pytest

from app.services import session_store


@pytest.fixture(autouse=True)
def _reset_sessions():
    """각 테스트 시작 전에 인메모리 세션 저장소를 비운다.

    _sessions는 모듈 전역 딕셔너리라, 이전 테스트에서 쌓인 데이터가
    다음 테스트로 새어 들어가는 것을 막아야 테스트 간 독립성이 보장된다.
    """
    session_store._sessions.clear()
    yield
    session_store._sessions.clear()


def test_get_history_returns_empty_list_for_unknown_session():
    assert session_store.get_history("no-such-session") == []


def test_append_turn_then_get_history_returns_it():
    session_store.append_turn("s1", question="주문 수는?", sql="SELECT 1", summary="1건")

    history = session_store.get_history("s1")

    assert len(history) == 1
    assert history[0]["question"] == "주문 수는?"
    assert history[0]["sql"] == "SELECT 1"
    assert history[0]["summary"] == "1건"


def test_history_preserves_insertion_order():
    session_store.append_turn("s1", question="첫번째", sql="SELECT 1", summary="")
    session_store.append_turn("s1", question="두번째", sql="SELECT 2", summary="")
    session_store.append_turn("s1", question="세번째", sql="SELECT 3", summary="")

    history = session_store.get_history("s1")

    assert [turn["question"] for turn in history] == ["첫번째", "두번째", "세번째"]


def test_sessions_are_isolated_from_each_other():
    session_store.append_turn("s1", question="세션1 질문", sql="SELECT 1", summary="")
    session_store.append_turn("s2", question="세션2 질문", sql="SELECT 2", summary="")

    assert len(session_store.get_history("s1")) == 1
    assert len(session_store.get_history("s2")) == 1
    assert session_store.get_history("s1")[0]["question"] == "세션1 질문"
    assert session_store.get_history("s2")[0]["question"] == "세션2 질문"


def test_history_is_trimmed_to_max_size():
    max_size = session_store._MAX_HISTORY_PER_SESSION

    for i in range(max_size + 5):
        session_store.append_turn("s1", question=f"질문{i}", sql=f"SELECT {i}", summary="")

    history = session_store.get_history("s1")

    # 오래된 턴부터 잘려나가서, 항상 최대 개수만 유지돼야 한다.
    assert len(history) == max_size
    # 가장 최근 턴(마지막으로 추가한 것)은 남아 있어야 한다.
    assert history[-1]["question"] == f"질문{max_size + 4}"
    # 가장 오래된 턴(질문0)은 잘려나가고 없어야 한다.
    assert history[0]["question"] != "질문0"
