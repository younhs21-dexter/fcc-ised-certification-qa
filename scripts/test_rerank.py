# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from rag_system import VectorSearch

print('Loading with reranker...')
search = VectorSearch(use_reranker=True)
print('Reranker loaded:', search.reranker is not None)

print('\n=== Part 15E (Hybrid + Rerank) ===')
results = search.search('Part 15E', n_results=5, hybrid=True, rerank=True)
for i, r in enumerate(results):
    print(f'  [{i+1}] {r.doc_id} ({r.source_type}) - {(1-r.distance)*100:.1f}%')

print('\n=== Part 15E (Hybrid only) ===')
results2 = search.search('Part 15E', n_results=5, hybrid=True, rerank=False)
for i, r in enumerate(results2):
    print(f'  [{i+1}] {r.doc_id} ({r.source_type}) - {(1-r.distance)*100:.1f}%')
