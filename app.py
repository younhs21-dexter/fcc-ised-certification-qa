"""
FCC/ISED 인증 Q&A 시스템 - Web UI
Streamlit 기반 웹 인터페이스
"""

import streamlit as st
import sys
import json
from pathlib import Path
from datetime import datetime

# 스크립트 경로 추가
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from rag_system import RAGSystem, MockLLMBackend, OllamaBackend, ClaudeBackend

# 페이지 설정
st.set_page_config(
    page_title="FCC/ISED 인증 Q&A",
    page_icon="📡",
    layout="wide"
)

# 세션 상태 초기화
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'last_response' not in st.session_state:
    st.session_state.last_response = None
if 'feedback_submitted' not in st.session_state:
    st.session_state.feedback_submitted = False

# 피드백 저장 경로
FEEDBACK_FILE = Path(__file__).parent / "aidata" / "feedback.json"


def save_feedback(query: str, answer: str, sources: list, rating: int, comment: str):
    """피드백 저장"""
    feedback_data = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "answer": answer[:500],  # 답변 일부만 저장
        "sources": [{"doc_id": s.doc_id, "source_type": s.source_type} for s in sources[:3]],
        "rating": rating,
        "comment": comment
    }

    # 기존 피드백 로드
    feedbacks = []
    if FEEDBACK_FILE.exists():
        try:
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                feedbacks = json.load(f)
        except:
            feedbacks = []

    # 새 피드백 추가
    feedbacks.append(feedback_data)

    # 저장
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(feedbacks, f, ensure_ascii=False, indent=2)

    return True


@st.cache_resource
def load_rag_system(backend_type: str = "mock", model: str = "qwen2:7b", api_key: str = None, use_reranker: bool = False):
    """RAG 시스템 로드 (캐싱)"""
    from rag_system import VectorSearch

    # 검색 엔진 초기화 (리랭커 옵션 포함)
    search_engine = VectorSearch(use_reranker=use_reranker)

    if backend_type == "ollama":
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                rag = RAGSystem(llm_backend=OllamaBackend(model=model))
                rag.search_engine = search_engine
                return rag
        except:
            st.warning("Ollama 연결 실패. Mock 모드로 전환됩니다.")
    elif backend_type == "claude":
        try:
            rag = RAGSystem(llm_backend=ClaudeBackend(api_key=api_key, model=model))
            rag.search_engine = search_engine
            return rag
        except Exception as e:
            st.error(f"Claude API 오류: {e}")

    rag = RAGSystem(llm_backend=MockLLMBackend())
    rag.search_engine = search_engine
    return rag


def main():
    # 헤더
    st.title("📡 FCC/ISED 인증 Q&A 시스템")
    st.markdown("---")

    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 설정")

        # LLM 선택
        llm_option = st.selectbox(
            "LLM 백엔드",
            [
                "Claude API (Sonnet)",
                "Claude API (Haiku)",
                "Ollama - Qwen2 (한국어)",
                "Ollama - Llama3 (영어)",
                "Mock (검색만)"
            ],
            help="Claude: 고품질 답변, Ollama: 로컬 무료"
        )

        # Claude API 키 입력
        api_key = None
        if "Claude" in llm_option:
            api_key = st.text_input(
                "Claude API Key",
                type="password",
                help="sk-ant-... 형식의 API 키",
                placeholder="sk-ant-api03-..."
            )
            if not api_key:
                st.warning("API 키를 입력하세요")

        # 백엔드 설정
        if "Claude" in llm_option:
            backend_type = "claude"
            if "Haiku" in llm_option:
                model = "claude-3-5-haiku-20241022"
            else:
                model = "claude-3-5-sonnet-20241022"
        elif "Ollama" in llm_option:
            backend_type = "ollama"
            model = "qwen2:7b" if "Qwen2" in llm_option else "llama3"
        else:
            backend_type = "mock"
            model = None

        # 검색 결과 수
        n_results = st.slider("검색 결과 수", 3, 10, 5)

        # 검색 옵션
        use_hybrid = st.checkbox("하이브리드 검색 (BM25+Vector)", value=True,
                                 help="키워드+의미 검색 결합. Part 15E 같은 정확한 검색에 효과적")
        use_rerank = st.checkbox("리랭킹 (CrossEncoder)", value=False,
                                 help="검색 결과 재정렬. 더 정확하지만 느림")

        # 컬렉션 선택
        st.subheader("검색 대상")
        search_kdb = st.checkbox("FCC KDB", value=True)
        search_ecfr = st.checkbox("eCFR (47 CFR)", value=True)
        search_rss = st.checkbox("ISED RSS", value=True)
        search_testreport = st.checkbox("Test Reports", value=True)

        collections = []
        if search_kdb:
            collections.append("fcc_kdb")
        if search_ecfr:
            collections.append("fcc_ecfr")
        if search_rss:
            collections.append("ised_rss")
        if search_testreport:
            collections.append("fcc_testreport")

        st.markdown("---")
        st.markdown("""
        ### 📚 데이터 소스
        - **KDB**: 32개 문서 (4,865 청크)
        - **eCFR**: 17개 Part (9,612 청크)
        - **RSS**: 34개 규격 (1,315 청크)
        - **Test Reports**: 5개 (807 청크)
        """)

        # 시스템 초기화
        if st.button("🔄 시스템 재로드"):
            st.cache_resource.clear()
            st.rerun()

    # RAG 시스템 로드
    with st.spinner("시스템 로딩 중..."):
        rag = load_rag_system(backend_type, model, api_key, use_rerank)

    # 메인 영역
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("💬 질문하기")

        # 질문 입력
        query = st.text_input(
            "질문을 입력하세요",
            placeholder="예: DFS 테스트 절차는 어떻게 되나요?",
            key="query_input"
        )

        # 예시 질문
        st.markdown("**예시 질문:**")
        example_cols = st.columns(3)
        examples = [
            "DFS 테스트 절차",
            "모듈 인증 요구사항",
            "RF 노출 제한"
        ]
        for i, ex in enumerate(examples):
            if example_cols[i].button(ex, key=f"ex_{i}"):
                query = ex

        # 검색 실행
        if query:
            search_mode = "검색 중..."
            if use_hybrid and use_rerank:
                search_mode = "하이브리드 + 리랭킹 중..."
            elif use_hybrid:
                search_mode = "하이브리드 검색 중..."
            elif use_rerank:
                search_mode = "리랭킹 검색 중..."

            with st.spinner(search_mode):
                # Q&A 검색 먼저
                qa_matches = rag.search_engine.search_qa(query, n_results=2, threshold=0.5)

                # 문서 검색 수행
                search_results = rag.search_engine.search(
                    query,
                    collections=collections if collections else None,
                    n_results=n_results,
                    hybrid=use_hybrid,
                    rerank=use_rerank
                )

            # Q&A 매칭 결과 표시
            if qa_matches:
                st.markdown("---")
                st.subheader("💡 관련 Q&A (검증된 답변)")
                for i, qa in enumerate(qa_matches):
                    similarity = qa['similarity'] * 100
                    with st.expander(f"Q: {qa['question'][:60]}... ({similarity:.0f}% 매칭)", expanded=(i == 0)):
                        st.markdown(f"**질문:** {qa['question']}")
                        st.markdown(f"**답변:** {qa['answer']}")
                        st.caption(f"출처: {qa['source_doc_id']} | 카테고리: {qa['category']}")

            # 문서 검색 결과 표시
            st.markdown("---")
            st.subheader("🔍 검색 결과")

            if not search_results:
                st.warning("검색 결과가 없습니다.")
            else:
                for i, result in enumerate(search_results):
                    similarity = (1 - result.distance) * 100

                    with st.expander(
                        f"[{i+1}] {result.doc_id} - 유사도: {similarity:.1f}%",
                        expanded=(i == 0)
                    ):
                        st.markdown(f"**파일:** `{result.source_file}`")
                        st.markdown(f"**유형:** {result.source_type.upper()}")
                        st.markdown("**내용:**")
                        st.text_area(
                            "content",
                            result.content,
                            height=150,
                            key=f"result_{i}",
                            label_visibility="collapsed"
                        )

                # LLM 답변 (Ollama 또는 Claude 사용 시)
                if backend_type in ["ollama", "claude"] and (backend_type != "claude" or api_key):
                    st.markdown("---")
                    st.subheader("🤖 AI 답변")
                    with st.spinner("답변 생성 중..."):
                        response = rag.ask(query, n_results=n_results)
                        st.markdown(response.answer)
                        st.session_state.last_response = response
                        st.session_state.feedback_submitted = False

                    # 피드백 UI
                    st.markdown("---")
                    st.subheader("📝 답변 평가")

                    col_rating, col_comment = st.columns([1, 2])

                    with col_rating:
                        rating = st.radio(
                            "답변 품질 (1-5점)",
                            options=[1, 2, 3, 4, 5],
                            format_func=lambda x: "⭐" * x,
                            horizontal=True,
                            key="rating_input"
                        )

                    with col_comment:
                        comment = st.text_area(
                            "코멘트 (선택사항)",
                            placeholder="어떤 점이 좋았거나 부족했나요? 원하는 답변은 무엇이었나요?",
                            height=80,
                            key="comment_input"
                        )

                    if st.button("✅ 피드백 제출", type="primary"):
                        if st.session_state.last_response:
                            save_feedback(
                                query=query,
                                answer=response.answer,
                                sources=search_results,
                                rating=rating,
                                comment=comment
                            )
                            st.success(f"피드백이 저장되었습니다! (평점: {'⭐' * rating})")
                            st.session_state.feedback_submitted = True

                elif backend_type == "claude" and not api_key:
                    st.warning("⚠️ Claude API 키를 입력해야 AI 답변을 받을 수 있습니다.")
                else:
                    st.info("💡 AI 답변을 보려면 Ollama 또는 Claude API를 선택하세요.")

    with col2:
        st.subheader("📊 시스템 상태")

        # 통계
        stats = {
            "KDB 문서": "32개 KDB (4,865)",
            "eCFR": "17개 Part (9,612)",
            "RSS": "34개 규격 (1,315)",
            "Test Report": "5개 (807)",
            "총 청크": "16,599개"
        }

        for key, value in stats.items():
            st.metric(key, value)

        st.markdown("---")

        # 검색 히스토리
        st.subheader("📝 최근 검색")
        if query and query not in st.session_state.chat_history:
            st.session_state.chat_history.append(query)
            # 최근 10개만 유지
            st.session_state.chat_history = st.session_state.chat_history[-10:]

        for q in reversed(st.session_state.chat_history[-5:]):
            st.text(f"• {q}")


if __name__ == "__main__":
    main()
