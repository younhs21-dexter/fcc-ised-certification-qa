# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from rag_system import VectorSearch

search = VectorSearch(use_reranker=False)

# 캐시 완전 초기화
search.bm25_index = {}
search.doc_cache = {}

# Test Report만 검색
print('=== Test Report Only ===')
queries = ['UNII', 'Bluetooth', 'UWB', 'WWAN', 'wifi', '6e wlan', 'bt test']
for q in queries:
    print(f'\n[{q}]')
    results = search.search(q, collections=['fcc_testreport'], n_results=3, hybrid=True)
    for i, r in enumerate(results):
        print(f'  {i+1}. {r.doc_id[:50]} - {(1-r.distance)*100:.1f}%')

# 전체 검색
print('\n\n=== All Collections ===')
for q in ['UNII WLAN', 'Bluetooth test report', 'UWB measurement']:
    print(f'\n[{q}]')
    results = search.search(q, n_results=5, hybrid=True)
    for i, r in enumerate(results):
        print(f'  {i+1}. {r.doc_id[:40]} ({r.source_type}) - {(1-r.distance)*100:.1f}%')
