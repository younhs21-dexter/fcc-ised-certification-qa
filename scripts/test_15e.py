# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from rag_system import RAGSystem, MockLLMBackend

rag = RAGSystem(llm_backend=MockLLMBackend())

queries = ['FCC part 15E', 'UNII', '15.407', 'U-NII device']
for query in queries:
    print(f'\n=== {query} ===')
    results = rag.search_engine.search(query, n_results=5)
    for i, r in enumerate(results):
        print(f'[{i+1}] {r.doc_id} ({r.source_type}) - {(1-r.distance)*100:.1f}%')
