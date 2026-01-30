# -*- coding: utf-8 -*-
"""하이브리드 검색 테스트"""
import sys
sys.path.insert(0, '.')
from rag_system import RAGSystem, MockLLMBackend

print("RAG System loading...")
rag = RAGSystem(llm_backend=MockLLMBackend())

queries = ['FCC part 15E', 'Part 15E UNII', '15.407', 'U-NII 5GHz power limit']

for query in queries:
    print(f'\n=== Query: {query} ===')

    # 하이브리드 검색 (기본값)
    results = rag.search_engine.search(query, n_results=5, hybrid=True)
    print('Hybrid (vector 50% + BM25 50%):')
    for i, r in enumerate(results[:3]):
        print(f'  [{i+1}] {r.doc_id} ({r.source_type}) - score: {(1-r.distance)*100:.1f}%')
