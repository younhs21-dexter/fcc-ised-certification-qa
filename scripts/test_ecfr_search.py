# -*- coding: utf-8 -*-
"""eCFR 검색 테스트"""
import sys
sys.path.insert(0, '.')

from rag_system import RAGSystem, MockLLMBackend

print("RAG System loading...")
rag = RAGSystem(llm_backend=MockLLMBackend())

queries = [
    'Class B digital device limit',
    'unintentional radiator',
    'spurious emission limit dBm'
]

for query in queries:
    print(f'\n=== Query: {query} ===')
    results = rag.search_engine.search(query, n_results=5)
    for i, r in enumerate(results):
        print(f'  [{i+1}] {r.source_type}: {r.doc_id} (sim: {(1-r.distance)*100:.1f}%)')
