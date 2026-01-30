# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from rag_system import VectorSearch

search = VectorSearch(use_reranker=False)
search.bm25_index = {}
search.doc_cache = {}

# RSS 검색 테스트
rss_queries = ['RSS-247', 'RSS 247', 'ISED RSS-247', 'low power device']
print('=== RSS 검색 테스트 ===')
for q in rss_queries:
    print(f'\n[{q}]')
    results = search.search(q, n_results=3, hybrid=True)
    for i, r in enumerate(results):
        print(f'  {i+1}. {r.doc_id} ({r.source_type}) - {(1-r.distance)*100:.1f}%')

# Test Report 검색 테스트
report_queries = ['UNII WLAN report', 'Bluetooth test', 'UWB FCC report', 'Part 24 WWAN']
print('\n\n=== Test Report 검색 테스트 ===')
for q in report_queries:
    print(f'\n[{q}]')
    results = search.search(q, n_results=3, hybrid=True)
    for i, r in enumerate(results):
        print(f'  {i+1}. {r.doc_id} ({r.source_type}) - {(1-r.distance)*100:.1f}%')
