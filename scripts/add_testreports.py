"""
Test Report만 벡터DB에 추가하는 스크립트
"""
import sys
sys.path.insert(0, str(__file__).replace('\\add_testreports.py', ''))

from vectordb_pipeline import process_testreport_documents, VectorDBBuilder, logger

def main():
    logger.info("Test Report 추가 시작")

    # Test Report 처리
    collection, chunks = process_testreport_documents()

    if chunks > 0:
        logger.info(f"\n완료: {chunks}개 청크 추가됨")

        # 검색 테스트
        logger.info("\n검색 테스트:")
        builder = VectorDBBuilder()

        test_queries = [
            "spurious emission limit",
            "conducted power measurement",
            "antenna gain",
            "DFS radar detection",
            "channel bandwidth"
        ]

        for query in test_queries:
            logger.info(f"\n쿼리: '{query}'")
            results = builder.search(collection, query, n_results=2)

            for i, r in enumerate(results):
                doc_id = r['metadata']['doc_id'][:50]
                logger.info(f"  [{i+1}] {doc_id}... (거리: {r['distance']:.4f})")
    else:
        logger.warning("추가된 청크가 없습니다.")

if __name__ == '__main__':
    main()
