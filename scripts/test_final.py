# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from rag_system import VectorSearch

search = VectorSearch()
search.bm25_index = {}
search.doc_cache = {}

queries = ['Part 15E', 'FCC Part 15E', '15E', 'Subpart E UNII']
for query in queries:
    print(f'\n=== {query} ===')
    results = search.search(query, n_results=5, hybrid=True, vector_weight=0.3)
    for i, r in enumerate(results):
        print(f'  [{i+1}] {r.doc_id} ({r.source_type}) - {(1-r.distance)*100:.1f}%')
