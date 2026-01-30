# -*- coding: utf-8 -*-
"""하이브리드 검색 - BM25 가중치 테스트"""
import sys
sys.path.insert(0, '.')
from rag_system import VectorSearch

print("VectorSearch loading...")
search = VectorSearch()
search.bm25_index = {}  # 캐시 초기화
search.doc_cache = {}

query = 'Part 15E'
print(f'\nQuery: {query}')

# 다양한 가중치 테스트
for bm25_weight in [0.3, 0.5, 0.7, 0.9]:
    vector_weight = 1 - bm25_weight
    results = search.search(query, n_results=3, hybrid=True, vector_weight=vector_weight)
    print(f'\n  BM25 {bm25_weight*100:.0f}% / Vector {vector_weight*100:.0f}%:')
    for i, r in enumerate(results):
        print(f'    [{i+1}] {r.doc_id} - {(1-r.distance)*100:.1f}%')
