# -*- coding: utf-8 -*-
"""하이브리드 검색 테스트 2 - doc_id 포함"""
import sys
sys.path.insert(0, '.')

# 캐시 초기화를 위해 새로 임포트
from rag_system import VectorSearch, SearchResult

print("VectorSearch loading (fresh)...")
search = VectorSearch()

# BM25 캐시 강제 초기화
search.bm25_index = {}
search.doc_cache = {}

queries = ['FCC part 15E', 'Part 15E', 'CFR Part 15E', '15E UNII']

for query in queries:
    print(f'\n=== Query: {query} ===')
    results = search.search(query, n_results=5, hybrid=True)
    for i, r in enumerate(results[:5]):
        print(f'  [{i+1}] {r.doc_id} ({r.source_type}) - score: {(1-r.distance)*100:.1f}%')
