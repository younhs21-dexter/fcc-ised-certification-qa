"""RAG 시스템 간단 테스트"""
import sys
sys.path.insert(0, r"C:\Users\younh\Documents\Ai model\scripts")

from rag_system import RAGSystem, MockLLMBackend

print("=" * 60)
print("RAG 시스템 테스트")
print("=" * 60)

rag = RAGSystem(llm_backend=MockLLMBackend())

query = "DFS test procedure"
print(f"\n질문: {query}\n")

response = rag.ask(query, n_results=3)

print("검색 결과:")
for i, src in enumerate(response.sources):
    print(f"\n[{i+1}] {src.doc_id}")
    print(f"    파일: {src.source_file}")
    print(f"    유사도: {1 - src.distance:.2%}")
    print(f"    내용: {src.content[:200]}...")

print("\n" + "=" * 60)
print("테스트 완료!")
