# -*- coding: utf-8 -*-
"""
생성된 Q&A 쌍을 벡터DB에 저장
질문을 임베딩하여 검색 가능하게 함
"""

import json
import sys
import io
from pathlib import Path

# Windows 콘솔 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent.parent


def main():
    print("=" * 60)
    print("Q&A 벡터DB 저장")
    print("=" * 60)

    # 1. Q&A 파일 로드
    qa_file = BASE_DIR / "aidata" / "qa_pairs.json"
    if not qa_file.exists():
        print(f"❌ Q&A 파일이 없습니다: {qa_file}")
        print("   먼저 generate_qa_pairs.py를 실행하세요.")
        return

    with open(qa_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    qa_pairs = data.get('qa_pairs', [])
    print(f"📄 로드된 Q&A: {len(qa_pairs)}개")

    if not qa_pairs:
        print("❌ Q&A가 없습니다.")
        return

    # 2. ChromaDB 및 임베딩 모델 초기화
    import chromadb
    from sentence_transformers import SentenceTransformer

    print("🔄 임베딩 모델 로딩...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    client = chromadb.PersistentClient(path=str(BASE_DIR / "aidata" / "vector_db"))

    # 기존 컬렉션 삭제 후 재생성
    collection_name = "qa_pairs"
    try:
        client.delete_collection(collection_name)
        print(f"   기존 {collection_name} 컬렉션 삭제")
    except:
        pass

    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Generated Q&A pairs for RF certification"}
    )
    print(f"✅ 컬렉션 생성: {collection_name}")

    # 3. Q&A 임베딩 및 저장
    print("🔄 Q&A 임베딩 중...")

    ids = []
    documents = []  # 질문을 document로 저장
    metadatas = []
    embeddings = []

    for i, qa in enumerate(qa_pairs):
        question = qa.get('question', '')
        answer = qa.get('answer', '')

        if not question or not answer:
            continue

        # ID 생성
        qa_id = f"qa_{i:04d}"
        ids.append(qa_id)

        # 질문을 document로 저장 (검색 대상)
        documents.append(question)

        # 메타데이터에 답변 및 출처 저장
        metadatas.append({
            'answer': answer,
            'category': qa.get('category', ''),
            'source_doc_id': qa.get('source_doc_id', ''),
            'source_type': qa.get('source_type', ''),
            'source_file': qa.get('source_file', '')
        })

        # 질문 임베딩
        embedding = model.encode(question).tolist()
        embeddings.append(embedding)

        if (i + 1) % 20 == 0:
            print(f"   {i + 1}/{len(qa_pairs)} 처리됨...")

    # 4. 배치로 저장
    print("💾 벡터DB에 저장 중...")

    # ChromaDB는 한 번에 최대 5461개까지 추가 가능
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        end = min(i + batch_size, len(ids))
        collection.add(
            ids=ids[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end],
            embeddings=embeddings[i:end]
        )

    print(f"\n{'=' * 60}")
    print(f"✅ 완료!")
    print(f"   - 저장된 Q&A: {len(ids)}개")
    print(f"   - 컬렉션: {collection_name}")
    print(f"{'=' * 60}")

    # 5. 테스트 검색
    print("\n🔍 테스트 검색:")
    test_queries = [
        "UNII 출력 제한",
        "DFS 요구사항",
        "RSS-247 적용 범위"
    ]

    for query in test_queries:
        query_embedding = model.encode(query).tolist()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=1
        )

        if results['documents'][0]:
            print(f"\n  Q: {query}")
            print(f"  → 매칭된 질문: {results['documents'][0][0][:50]}...")
            print(f"  → 답변: {results['metadatas'][0][0]['answer'][:80]}...")


if __name__ == "__main__":
    main()
