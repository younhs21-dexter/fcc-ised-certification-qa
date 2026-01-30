"""한국어 RAG 테스트 - Qwen2"""
import sys
sys.path.insert(0, r"C:\Users\younh\Documents\Ai model\scripts")

from rag_system import RAGSystem, OllamaBackend

print("=" * 60)
print("한국어 RAG 테스트 (Qwen2 7B)")
print("=" * 60)

# Qwen2 백엔드로 RAG 시스템 초기화
print("\n시스템 초기화 중...")
rag = RAGSystem(llm_backend=OllamaBackend(model="qwen2:7b"))

# 한국어 질문
query = "DFS 테스트 절차에 대해 설명해주세요"
print(f"\n질문: {query}")
print("\n답변 생성 중...")

response = rag.ask(query, n_results=3)

print("\n" + "=" * 60)
print("답변:")
print("=" * 60)
print(response.answer)

print("\n" + "-" * 60)
print("참고 문서:")
for i, src in enumerate(response.sources[:3]):
    print(f"  [{i+1}] {src.doc_id} (유사도: {1-src.distance:.1%})")
