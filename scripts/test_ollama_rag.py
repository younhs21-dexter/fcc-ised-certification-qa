"""Ollama + RAG 통합 테스트"""
import sys
sys.path.insert(0, r"C:\Users\younh\Documents\Ai model\scripts")

from rag_system import RAGSystem, OllamaBackend

print("=" * 60)
print("Ollama + RAG 통합 테스트")
print("=" * 60)

# Ollama 백엔드로 RAG 시스템 초기화
print("\n1. RAG 시스템 초기화 중...")
rag = RAGSystem(llm_backend=OllamaBackend(model="llama3"))
print("   완료!")

# 테스트 질문
query = "What is DFS test procedure?"
print(f"\n2. 질문: {query}")
print("\n3. 답변 생성 중... (GPU 사용)")

response = rag.ask(query, n_results=3)

print("\n" + "=" * 60)
print("답변:")
print("=" * 60)
print(response.answer)

print("\n" + "-" * 60)
print("참고 문서:")
print("-" * 60)
for i, src in enumerate(response.sources[:3]):
    print(f"[{i+1}] {src.doc_id} (유사도: {1-src.distance:.1%})")
