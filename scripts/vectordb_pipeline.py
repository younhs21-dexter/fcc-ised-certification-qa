"""
AI 자동화 시스템 - 벡터DB 파이프라인
2단계: 문서 → 텍스트 추출 → 청킹 → 임베딩 → ChromaDB 저장
"""

import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Generator
from dataclasses import dataclass, asdict

import fitz  # PyMuPDF
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# 경로 설정
BASE_DIR = Path(r"C:\Users\younh\Documents\Ai model")
RAW_DATA_DIR = BASE_DIR / "aidata" / "raw_data"
VECTOR_DB_DIR = BASE_DIR / "aidata" / "vector_db"
LOGS_DIR = BASE_DIR / "logs"

VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "vectordb.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """텍스트 청크 데이터 구조"""
    chunk_id: str
    source_file: str
    source_type: str  # kdb, ecfr, rss
    doc_id: str
    page_num: Optional[int]
    chunk_index: int
    content: str
    metadata: Dict


class PDFExtractor:
    """
    PDF 텍스트 추출기
    - PyMuPDF 사용
    - 페이지별 텍스트 추출
    - 테이블 구조 보존 시도
    """

    def extract(self, pdf_path: Path) -> List[Dict]:
        """PDF에서 텍스트 추출"""
        pages = []

        try:
            doc = fitz.open(pdf_path)
            for page_num, page in enumerate(doc):
                text = page.get_text("text")
                # 빈 페이지 건너뛰기
                if text.strip():
                    pages.append({
                        'page_num': page_num + 1,
                        'content': self._clean_text(text)
                    })
            doc.close()
            logger.info(f"Extracted {len(pages)} pages from {pdf_path.name}")
        except Exception as e:
            logger.error(f"Failed to extract {pdf_path}: {e}")

        return pages

    def _clean_text(self, text: str) -> str:
        """텍스트 정리"""
        # 연속 공백 정리
        text = re.sub(r'[ \t]+', ' ', text)
        # 연속 줄바꿈 정리
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


class TextChunker:
    """
    텍스트 청킹기
    - 의미 단위로 분할
    - 오버랩 적용으로 컨텍스트 유지
    """

    def __init__(self, chunk_size: int = 800, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, metadata: Dict) -> List[TextChunk]:
        """텍스트를 청크로 분할"""
        chunks = []

        # 문단 단위로 먼저 분할
        paragraphs = self._split_paragraphs(text)

        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            # 현재 청크 + 새 문단이 크기 제한 초과
            if len(current_chunk) + len(para) > self.chunk_size:
                if current_chunk:
                    chunks.append(self._create_chunk(
                        current_chunk, chunk_index, metadata
                    ))
                    chunk_index += 1

                    # 오버랩: 마지막 부분 유지
                    if len(current_chunk) > self.overlap:
                        current_chunk = current_chunk[-self.overlap:] + "\n" + para
                    else:
                        current_chunk = para
                else:
                    # 단일 문단이 크기 초과 - 강제 분할
                    for sub_chunk in self._force_split(para):
                        chunks.append(self._create_chunk(
                            sub_chunk, chunk_index, metadata
                        ))
                        chunk_index += 1
                    current_chunk = ""
            else:
                current_chunk += "\n" + para if current_chunk else para

        # 마지막 청크
        if current_chunk.strip():
            chunks.append(self._create_chunk(
                current_chunk, chunk_index, metadata
            ))

        return chunks

    def _split_paragraphs(self, text: str) -> List[str]:
        """문단 분할"""
        # 두 줄 이상 공백으로 분리
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _force_split(self, text: str) -> List[str]:
        """강제 분할 (긴 문단)"""
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.overlap):
            chunks.append(text[i:i + self.chunk_size])
        return chunks

    def _create_chunk(self, content: str, index: int, metadata: Dict) -> TextChunk:
        """청크 객체 생성"""
        # 고유 ID 생성: doc_id + 파일명 해시 + 페이지 + 인덱스
        import hashlib
        source_file = metadata.get('source_file', 'unknown')
        file_hash = hashlib.md5(source_file.encode()).hexdigest()[:8]
        page_num = metadata.get('page_num', 0)
        chunk_id = f"{metadata.get('doc_id', 'unknown')}_{file_hash}_p{page_num}_{index:04d}"

        return TextChunk(
            chunk_id=chunk_id,
            source_file=source_file,
            source_type=metadata.get('source_type', 'unknown'),
            doc_id=metadata.get('doc_id', ''),
            page_num=metadata.get('page_num'),
            chunk_index=index,
            content=content.strip(),
            metadata=metadata
        )


class VectorDBBuilder:
    """
    벡터DB 구축기
    - SentenceTransformers로 임베딩
    - ChromaDB에 저장
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name

        # ChromaDB 초기화
        self.client = chromadb.PersistentClient(
            path=str(VECTOR_DB_DIR),
            settings=Settings(anonymized_telemetry=False)
        )

    def get_or_create_collection(self, name: str) -> chromadb.Collection:
        """컬렉션 생성 또는 가져오기"""
        return self.client.get_or_create_collection(
            name=name,
            metadata={"model": self.model_name}
        )

    def add_chunks(self, collection: chromadb.Collection, chunks: List[TextChunk], batch_size: int = 50):
        """청크를 벡터DB에 추가"""
        if not chunks:
            return

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            ids = [c.chunk_id for c in batch]
            documents = [c.content for c in batch]
            metadatas = [
                {
                    'source_file': c.source_file,
                    'source_type': c.source_type,
                    'doc_id': c.doc_id,
                    'page_num': c.page_num or 0,
                    'chunk_index': c.chunk_index
                }
                for c in batch
            ]

            # 임베딩 생성
            embeddings = self.model.encode(documents).tolist()

            # ChromaDB에 추가
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )

            logger.info(f"Added batch {i//batch_size + 1}: {len(batch)} chunks")

    def search(self, collection: chromadb.Collection, query: str, n_results: int = 5) -> List[Dict]:
        """유사도 검색"""
        query_embedding = self.model.encode([query]).tolist()

        results = collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )

        return [
            {
                'id': results['ids'][0][i],
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            }
            for i in range(len(results['ids'][0]))
        ]


def process_kdb_documents():
    """KDB 문서 처리"""
    logger.info("=" * 60)
    logger.info("KDB 문서 벡터화 시작")
    logger.info("=" * 60)

    extractor = PDFExtractor()
    chunker = TextChunker(chunk_size=800, overlap=100)
    builder = VectorDBBuilder()

    collection = builder.get_or_create_collection("fcc_kdb")

    kdb_dir = RAW_DATA_DIR / "kdb"
    total_chunks = 0
    processed_docs = 0

    for kdb_folder in kdb_dir.iterdir():
        if not kdb_folder.is_dir():
            continue

        kdb_number = kdb_folder.name.replace("KDB_", "")
        logger.info(f"\nProcessing KDB {kdb_number}")

        for pdf_file in kdb_folder.glob("*.pdf"):
            # 텍스트 추출
            pages = extractor.extract(pdf_file)

            all_chunks = []
            for page in pages:
                metadata = {
                    'source_file': pdf_file.name,
                    'source_type': 'kdb',
                    'doc_id': f"KDB_{kdb_number}",
                    'page_num': page['page_num']
                }
                chunks = chunker.chunk(page['content'], metadata)
                all_chunks.extend(chunks)

            # 벡터DB에 추가
            if all_chunks:
                builder.add_chunks(collection, all_chunks)
                total_chunks += len(all_chunks)
                processed_docs += 1

    logger.info(f"\n{'='*60}")
    logger.info(f"KDB 처리 완료: {processed_docs}개 문서, {total_chunks}개 청크")
    logger.info(f"{'='*60}")

    return collection, total_chunks


def process_ecfr_documents():
    """eCFR 문서 처리"""
    logger.info("=" * 60)
    logger.info("eCFR 문서 벡터화 시작")
    logger.info("=" * 60)

    chunker = TextChunker(chunk_size=800, overlap=100)
    builder = VectorDBBuilder()

    collection = builder.get_or_create_collection("fcc_ecfr")

    ecfr_dir = RAW_DATA_DIR / "ecfr"
    total_chunks = 0

    for txt_file in ecfr_dir.glob("*.txt"):
        logger.info(f"Processing {txt_file.name}")

        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        metadata = {
            'source_file': txt_file.name,
            'source_type': 'ecfr',
            'doc_id': txt_file.stem
        }

        chunks = chunker.chunk(content, metadata)

        if chunks:
            builder.add_chunks(collection, chunks)
            total_chunks += len(chunks)

    logger.info(f"\neCFR 처리 완료: {total_chunks}개 청크")

    return collection, total_chunks


def process_rss_documents():
    """RSS 문서 처리"""
    logger.info("=" * 60)
    logger.info("RSS 문서 벡터화 시작")
    logger.info("=" * 60)

    chunker = TextChunker(chunk_size=800, overlap=100)
    builder = VectorDBBuilder()

    collection = builder.get_or_create_collection("ised_rss")

    rss_dir = RAW_DATA_DIR / "rss"
    total_chunks = 0

    for txt_file in rss_dir.glob("*.txt"):
        logger.info(f"Processing {txt_file.name}")

        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        metadata = {
            'source_file': txt_file.name,
            'source_type': 'rss',
            'doc_id': txt_file.stem
        }

        chunks = chunker.chunk(content, metadata)

        if chunks:
            builder.add_chunks(collection, chunks)
            total_chunks += len(chunks)

    logger.info(f"\nRSS 처리 완료: {total_chunks}개 청크")

    return collection, total_chunks


def process_testreport_documents():
    """Test Report 문서 처리"""
    logger.info("=" * 60)
    logger.info("Test Report 문서 벡터화 시작")
    logger.info("=" * 60)

    extractor = PDFExtractor()
    chunker = TextChunker(chunk_size=800, overlap=100)
    builder = VectorDBBuilder()

    collection = builder.get_or_create_collection("fcc_testreport")

    testreport_dir = BASE_DIR / "aidata" / "Testreport"
    total_chunks = 0
    processed_docs = 0

    if not testreport_dir.exists():
        logger.warning(f"Test Report 폴더가 없습니다: {testreport_dir}")
        return None, 0

    for pdf_file in testreport_dir.glob("*.pdf"):
        logger.info(f"\nProcessing {pdf_file.name}")

        # 파일명에서 리포트 타입 추출
        # 예: S-4791615583-E11V1 FCC Report UNII(6E) WLAN.pdf
        report_name = pdf_file.stem

        # 텍스트 추출
        pages = extractor.extract(pdf_file)

        all_chunks = []
        for page in pages:
            metadata = {
                'source_file': pdf_file.name,
                'source_type': 'testreport',
                'doc_id': report_name,
                'page_num': page['page_num']
            }
            chunks = chunker.chunk(page['content'], metadata)
            all_chunks.extend(chunks)

        # 벡터DB에 추가
        if all_chunks:
            builder.add_chunks(collection, all_chunks)
            total_chunks += len(all_chunks)
            processed_docs += 1
            logger.info(f"  -> {len(all_chunks)}개 청크 추가")

    logger.info(f"\n{'='*60}")
    logger.info(f"Test Report 처리 완료: {processed_docs}개 문서, {total_chunks}개 청크")
    logger.info(f"{'='*60}")

    return collection, total_chunks


def test_search():
    """검색 테스트"""
    logger.info("\n" + "=" * 60)
    logger.info("검색 테스트")
    logger.info("=" * 60)

    builder = VectorDBBuilder()

    # KDB 검색 테스트
    kdb_collection = builder.get_or_create_collection("fcc_kdb")

    test_queries = [
        "DFS test procedure",
        "module certification requirements",
        "RF exposure limits"
    ]

    for query in test_queries:
        logger.info(f"\n쿼리: '{query}'")
        results = builder.search(kdb_collection, query, n_results=3)

        for i, r in enumerate(results):
            logger.info(f"  [{i+1}] {r['metadata']['doc_id']} (거리: {r['distance']:.4f})")
            logger.info(f"      {r['document'][:100]}...")


def main():
    """메인 실행"""
    logger.info("벡터DB 파이프라인 시작")
    logger.info(f"저장 위치: {VECTOR_DB_DIR}")

    # KDB 처리
    kdb_collection, kdb_chunks = process_kdb_documents()

    # eCFR 처리
    ecfr_collection, ecfr_chunks = process_ecfr_documents()

    # RSS 처리
    rss_collection, rss_chunks = process_rss_documents()

    # Test Report 처리
    testreport_collection, testreport_chunks = process_testreport_documents()

    # 요약
    logger.info("\n" + "=" * 60)
    logger.info("벡터DB 구축 완료")
    logger.info("=" * 60)
    logger.info(f"KDB: {kdb_chunks}개 청크")
    logger.info(f"eCFR: {ecfr_chunks}개 청크")
    logger.info(f"RSS: {rss_chunks}개 청크")
    logger.info(f"Test Report: {testreport_chunks}개 청크")
    logger.info(f"총: {kdb_chunks + ecfr_chunks + rss_chunks + testreport_chunks}개 청크")

    # 검색 테스트
    test_search()

    return {
        'kdb_chunks': kdb_chunks,
        'ecfr_chunks': ecfr_chunks,
        'rss_chunks': rss_chunks,
        'testreport_chunks': testreport_chunks,
        'total': kdb_chunks + ecfr_chunks + rss_chunks + testreport_chunks
    }


if __name__ == '__main__':
    main()
