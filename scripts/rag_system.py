"""
AI 자동화 시스템 - RAG (Retrieval-Augmented Generation) 시스템
3단계: 벡터 검색 + LLM 연동으로 Q&A 기능 구현
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
import re

# 경로 설정
BASE_DIR = Path(r"C:\Users\younh\Documents\Ai model")
VECTOR_DB_DIR = BASE_DIR / "aidata" / "vector_db"
LOGS_DIR = BASE_DIR / "logs"

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "rag.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """검색 결과"""
    doc_id: str
    content: str
    source_file: str
    source_type: str
    distance: float


@dataclass
class RAGResponse:
    """RAG 응답"""
    answer: str
    sources: List[SearchResult]
    query: str
    qa_matches: List[dict] = None  # 매칭된 Q&A 쌍


class Reranker:
    """CrossEncoder 기반 리랭커"""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        logger.info(f"Loading reranker model: {model_name}")
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, results: List['SearchResult'], top_k: int = None) -> List['SearchResult']:
        """검색 결과 리랭킹"""
        if not results:
            return results

        # Query-Document 쌍 생성
        pairs = [(query, r.content) for r in results]

        # CrossEncoder 점수 계산
        scores = self.model.predict(pairs)

        # 점수와 결과 매핑
        scored_results = list(zip(scores, results))
        scored_results.sort(key=lambda x: x[0], reverse=True)  # 높은 점수 순

        # 새 distance 할당 (점수를 0~1로 정규화하여 distance로 변환)
        max_score = max(scores) if max(scores) > 0 else 1
        min_score = min(scores)
        score_range = max_score - min_score if max_score != min_score else 1

        reranked = []
        for score, result in scored_results:
            # 점수를 0~1로 정규화 후 distance로 변환
            norm_score = (score - min_score) / score_range
            result.distance = 1 - norm_score
            reranked.append(result)

        return reranked[:top_k] if top_k else reranked


class VectorSearch:
    """벡터 검색 엔진 (하이브리드 검색 + 리랭킹 지원)"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", use_reranker: bool = False):
        logger.info("Initializing Vector Search...")
        self.model = SentenceTransformer(model_name)

        # 리랭커 초기화 (옵션)
        self.reranker = None
        if use_reranker:
            try:
                self.reranker = Reranker()
            except Exception as e:
                logger.warning(f"Reranker 로드 실패: {e}")

        self.client = chromadb.PersistentClient(
            path=str(VECTOR_DB_DIR),
            settings=Settings(anonymized_telemetry=False)
        )

        # 컬렉션 로드
        self.collections = {}
        self.bm25_index = {}  # BM25 인덱스 캐시
        self.doc_cache = {}   # 문서 캐시

        for name in ["fcc_kdb", "fcc_ecfr", "ised_rss", "fcc_testreport"]:
            try:
                self.collections[name] = self.client.get_collection(name)
                count = self.collections[name].count()
                logger.info(f"  Loaded {name}: {count} documents")
            except Exception as e:
                logger.warning(f"  Collection {name} not found: {e}")

        # Q&A 컬렉션 로드
        self.qa_collection = None
        try:
            self.qa_collection = self.client.get_collection("qa_pairs")
            qa_count = self.qa_collection.count()
            logger.info(f"  Loaded qa_pairs: {qa_count} Q&A pairs")
        except Exception as e:
            logger.info(f"  Q&A collection not found (optional): {e}")

    def _tokenize(self, text: str) -> List[str]:
        """텍스트 토큰화 (BM25용)"""
        # 소문자 변환 + 특수문자/언더스코어를 공백으로 + 분리
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'_', ' ', text)  # 언더스코어도 분리
        tokens = text.split()
        return [t for t in tokens if len(t) > 1]  # 1글자 제외

    def _extract_keywords(self, doc_id: str, source_file: str, source_type: str) -> str:
        """문서에서 검색용 키워드 추출"""
        keywords = []

        # doc_id 추가
        keywords.append(doc_id)

        # source_file에서 키워드 추출
        keywords.append(source_file)

        # Test Report 특수 처리
        if source_type == 'testreport':
            # 파일명에서 기술 키워드 추출 (예: UNII, UWB, BT, WLAN, WWAN)
            file_lower = source_file.lower()
            if 'unii' in file_lower or '6e' in file_lower:
                keywords.extend(['unii', 'u-nii', '5ghz', '6ghz', 'wifi6e', 'wlan', 'part15e', '15e'])
            if 'uwb' in file_lower:
                keywords.extend(['uwb', 'ultra wideband', 'part15f', '15f'])
            if 'wwan' in file_lower or 'part 24' in file_lower or 'part24' in file_lower:
                keywords.extend(['wwan', 'lte', '4g', '5g', 'cellular', 'part24', '24e'])
            if 'dts' in file_lower or 'wlan' in file_lower:
                keywords.extend(['dts', 'wlan', 'wifi', '2.4ghz', 'part15c', '15c'])
            if 'bt' in file_lower or 'bluetooth' in file_lower:
                keywords.extend(['bt', 'bluetooth', 'ble', 'part15c', '15c'])
            # FCC Report 키워드
            keywords.extend(['fcc', 'test', 'report', 'measurement'])

        # RSS 특수 처리
        elif source_type == 'rss':
            keywords.extend(['ised', 'canada', 'ic', 'rss'])
            # RSS 번호 추출 (예: RSS-247 -> 247)
            import re
            rss_match = re.search(r'RSS[- ]?(\d+)', doc_id, re.IGNORECASE)
            if rss_match:
                keywords.append(rss_match.group(1))

        # eCFR 특수 처리
        elif source_type == 'ecfr':
            keywords.extend(['fcc', 'cfr', '47cfr', 'regulation'])
            # Part 번호 추출 (예: CFR_Part_15E -> 15E, 15, E)
            import re
            part_match = re.search(r'Part[_ ]?(\d+)([A-Z])?', doc_id, re.IGNORECASE)
            if part_match:
                keywords.append(part_match.group(1))  # 숫자만
                if part_match.group(2):
                    keywords.append(part_match.group(1) + part_match.group(2))  # 숫자+문자
                    keywords.append(part_match.group(2))  # 문자만

        # KDB 특수 처리
        elif source_type == 'kdb':
            keywords.extend(['kdb', 'guidance', 'fcc'])

        return ' '.join(keywords)

    def _build_bm25_index(self, col_name: str):
        """BM25 인덱스 구축 (한 번만 실행)"""
        if col_name in self.bm25_index:
            return

        logger.info(f"Building BM25 index for {col_name}...")
        col = self.collections[col_name]

        # 모든 문서 가져오기
        all_docs = col.get(include=['documents', 'metadatas'])

        # 토큰화 (doc_id, source_file, 추출 키워드 포함)
        tokenized_docs = []
        for i, doc in enumerate(all_docs['documents']):
            doc_id = all_docs['metadatas'][i].get('doc_id', '')
            source_file = all_docs['metadatas'][i].get('source_file', '')
            source_type = all_docs['metadatas'][i].get('source_type', '')

            # 키워드 추출
            keywords = self._extract_keywords(doc_id, source_file, source_type)

            # 키워드 + 원본 내용 결합
            combined = f"{keywords} {doc}"
            tokenized_docs.append(self._tokenize(combined))

        # BM25 인덱스 생성
        self.bm25_index[col_name] = BM25Okapi(tokenized_docs)
        self.doc_cache[col_name] = {
            'ids': all_docs['ids'],
            'documents': all_docs['documents'],
            'metadatas': all_docs['metadatas']
        }
        logger.info(f"  BM25 index built: {len(tokenized_docs)} documents")

    def search(self, query: str, collections: List[str] = None, n_results: int = 5,
               hybrid: bool = True, vector_weight: float = 0.5, rerank: bool = False) -> List[SearchResult]:
        """
        하이브리드 검색 (벡터 + BM25 독립 검색 후 병합) + 옵션 리랭킹

        Args:
            query: 검색어
            collections: 검색할 컬렉션 목록
            n_results: 반환할 결과 수
            hybrid: 하이브리드 검색 사용 여부
            vector_weight: 벡터 검색 가중치 (0~1, 나머지는 BM25)
            rerank: 리랭킹 적용 여부
        """
        if collections is None:
            collections = list(self.collections.keys())

        all_results = {}  # doc_id -> result (중복 제거용)

        for col_name in collections:
            if col_name not in self.collections:
                continue

            col = self.collections[col_name]

            # 1. 벡터 검색
            query_embedding = self.model.encode([query]).tolist()
            vector_results = col.query(
                query_embeddings=query_embedding,
                n_results=n_results * 3,
                include=['documents', 'metadatas', 'distances']
            )

            # 벡터 결과 저장
            for i in range(len(vector_results['ids'][0])):
                doc_id = vector_results['ids'][0][i]
                vector_dist = vector_results['distances'][0][i]
                vector_score = max(0, 1 - vector_dist)

                all_results[doc_id] = {
                    'doc_id': vector_results['metadatas'][0][i].get('doc_id', 'unknown'),
                    'content': vector_results['documents'][0][i],
                    'source_file': vector_results['metadatas'][0][i].get('source_file', ''),
                    'source_type': vector_results['metadatas'][0][i].get('source_type', ''),
                    'vector_score': vector_score,
                    'bm25_score': 0
                }

            if hybrid:
                # 2. BM25 독립 검색
                self._build_bm25_index(col_name)
                query_tokens = self._tokenize(query)
                bm25_scores = self.bm25_index[col_name].get_scores(query_tokens)
                cache = self.doc_cache[col_name]

                # BM25 상위 결과 가져오기
                max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
                top_bm25_indices = sorted(range(len(bm25_scores)),
                                         key=lambda x: bm25_scores[x], reverse=True)[:n_results * 3]

                for idx in top_bm25_indices:
                    doc_id = cache['ids'][idx]
                    bm25_norm = bm25_scores[idx] / max_bm25

                    if doc_id in all_results:
                        # 이미 벡터 검색에서 나온 결과 - BM25 점수 추가
                        all_results[doc_id]['bm25_score'] = bm25_norm
                    else:
                        # BM25에서만 나온 새 결과
                        all_results[doc_id] = {
                            'doc_id': cache['metadatas'][idx].get('doc_id', 'unknown'),
                            'content': cache['documents'][idx],
                            'source_file': cache['metadatas'][idx].get('source_file', ''),
                            'source_type': cache['metadatas'][idx].get('source_type', ''),
                            'vector_score': 0,
                            'bm25_score': bm25_norm
                        }

        # 3. 하이브리드 점수 계산 및 결과 생성
        final_results = []
        for doc_id, data in all_results.items():
            if hybrid:
                hybrid_score = (data['vector_score'] * vector_weight) + \
                              (data['bm25_score'] * (1 - vector_weight))
            else:
                hybrid_score = data['vector_score']

            final_results.append(SearchResult(
                doc_id=data['doc_id'],
                content=data['content'],
                source_file=data['source_file'],
                source_type=data['source_type'],
                distance=1 - hybrid_score  # 낮을수록 좋음
            ))

        # 거리 기준 정렬
        final_results.sort(key=lambda x: x.distance)

        # 리랭킹 적용 (옵션)
        if rerank and self.reranker:
            # 리랭킹을 위해 더 많은 후보를 가져옴
            candidates = final_results[:n_results * 2]
            final_results = self.reranker.rerank(query, candidates, top_k=n_results)

        return final_results[:n_results]

    def search_qa(self, query: str, n_results: int = 3, threshold: float = 0.6) -> List[dict]:
        """
        Q&A 컬렉션에서 검색

        Args:
            query: 검색어
            n_results: 반환할 Q&A 수
            threshold: 최소 유사도 (0~1, 높을수록 엄격)

        Returns:
            매칭된 Q&A 리스트 [{"question": ..., "answer": ..., "similarity": ...}, ...]
        """
        if not self.qa_collection:
            return []

        try:
            query_embedding = self.model.encode([query]).tolist()
            results = self.qa_collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )

            qa_matches = []
            for i in range(len(results['ids'][0])):
                distance = results['distances'][0][i]
                similarity = 1 - distance

                # 임계값 이상만 반환
                if similarity >= threshold:
                    qa_matches.append({
                        'question': results['documents'][0][i],
                        'answer': results['metadatas'][0][i].get('answer', ''),
                        'category': results['metadatas'][0][i].get('category', ''),
                        'source_doc_id': results['metadatas'][0][i].get('source_doc_id', ''),
                        'source_type': results['metadatas'][0][i].get('source_type', ''),
                        'similarity': similarity
                    })

            return qa_matches
        except Exception as e:
            logger.warning(f"Q&A search error: {e}")
            return []


class LLMBackend:
    """LLM 백엔드 추상 클래스"""

    def generate(self, prompt: str) -> str:
        raise NotImplementedError


class OllamaBackend(LLMBackend):
    """Ollama 로컬 LLM 백엔드"""

    def __init__(self, model: str = "qwen2:7b"):  # 기본값을 Qwen2로 변경 (한국어 지원)
        self.model = model
        self.base_url = "http://localhost:11434"

    def generate(self, prompt: str) -> str:
        import requests

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json().get('response', '')
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return f"[Ollama 오류: {e}]"


class ClaudeBackend(LLMBackend):
    """Anthropic Claude API 백엔드"""

    def __init__(self, api_key: str = None, model: str = "claude-3-5-sonnet-20241022"):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")

        from anthropic import Anthropic
        self.client = Anthropic(api_key=self.api_key)
        logger.info(f"Claude API initialized with model: {model}")

    def generate(self, prompt: str) -> str:
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return f"[Claude API 오류: {e}]"


class MockLLMBackend(LLMBackend):
    """테스트용 Mock LLM (LLM 없이 검색 결과만 반환)"""

    def generate(self, prompt: str) -> str:
        # 프롬프트에서 컨텍스트와 질문 추출해서 요약 형태로 반환
        return "[Mock LLM] 검색된 문서 기반으로 답변이 생성됩니다. 실제 LLM 연동 후 자연어 답변이 제공됩니다."


class RAGSystem:
    """RAG Q&A 시스템"""

    def __init__(self, llm_backend: LLMBackend = None):
        self.search_engine = VectorSearch()
        self.llm = llm_backend or MockLLMBackend()

    def build_prompt(self, query: str, contexts: List[SearchResult], qa_matches: List[dict] = None) -> str:
        """LLM 프롬프트 생성 - 구체적인 답변 유도"""

        # Q&A 매칭 결과 섹션
        qa_section = ""
        if qa_matches:
            qa_items = []
            for qa in qa_matches:
                qa_items.append(f"Q: {qa['question']}\nA: {qa['answer']}\n(출처: {qa['source_doc_id']})")
            qa_section = f"""
## 관련 Q&A (검증된 답변)

{chr(10).join(qa_items)}

---
"""

        context_text = "\n\n---\n\n".join([
            f"[출처: {c.doc_id} - {c.source_file}]\n{c.content}"
            for c in contexts
        ])

        prompt = f"""당신은 FCC/ISED RF 인증 시험 전문가입니다. 아래 참고 문서를 기반으로 질문에 **구체적이고 실용적으로** 답변하세요.
{qa_section}
## 참고 문서

{context_text}

## 질문

{query}

## 답변 작성 규칙 (필수)

### 1. 구체적인 수치 필수
- 출력 제한: dBm, W, mW, EIRP 단위로 명시 (예: "30 dBm (1W) EIRP")
- 주파수: MHz/GHz 단위로 정확히 (예: "5150-5250 MHz")
- 스퓨리어스/하모닉: dBc 또는 절대값으로 (예: "-20 dBc 또는 -40 dBm")
- 대역폭: 채널 대역폭, 측정 RBW 구분 (예: "RBW 1MHz, VBW 3MHz")

### 2. 규격 조항 정확히 인용
- FCC: "47 CFR § 15.407(a)(1)" 형식
- ISED: "RSS-247 Issue 2, Section 5.4" 형식
- KDB: "KDB 905462 D01 Section 7.2" 형식

### 3. 장비/운용 조건 구분
- Client vs Access Point (Master)
- Indoor only vs Indoor/Outdoor
- Fixed/Mobile/Portable 구분
- LPI(Low Power Indoor) vs SP(Standard Power) vs VLP(Very Low Power)

### 4. 측정 조건 명시
- 안테나: 거리(3m/10m), conducted/radiated
- Detector: Peak, Average, RMS
- 평균화 방법: 6dB 대역폭, 26dB 방출 대역폭

### 5. 문서에 없는 내용
- "참고 문서에서 확인되지 않음"으로 명시
- 추측하지 말 것

## 답변 형식

### [질문 주제 요약]

**적용 규격**
- 47 CFR Part 15 Subpart E (U-NII)
- RSS-247 Issue 2

**제한치 요약**

| 항목 | 요구사항 | 출처 |
|-----|---------|------|
| 최대 EIRP | 1W (30 dBm) | § 15.407(a)(1) |
| PSD | 17 dBm/MHz | § 15.407(a)(2) |
| DFS | 필수 (5250-5350, 5470-5725 MHz) | § 15.407(h) |

**측정 방법**
- RBW: 1 MHz (conducted), 1 MHz (radiated)
- Detector: Peak (스퓨리어스), Average (대역내)
- 거리: 3m (conducted power 계산용)

**참고 KDB/가이던스**
- KDB 905462: U-NII 측정 절차
- KDB 388624: DFS 테스트 가이던스

**주의사항**
- [특별히 주의할 점이 있으면 기재]

## 답변:
"""
        return prompt

    def ask(self, query: str, n_results: int = 5, hybrid: bool = True, rerank: bool = False) -> RAGResponse:
        """질문에 대한 답변 생성"""
        logger.info(f"Query: {query}")

        # 1. Q&A 검색 (유사 질문 매칭)
        qa_matches = self.search_engine.search_qa(query, n_results=2, threshold=0.5)
        if qa_matches:
            logger.info(f"Found {len(qa_matches)} matching Q&A pairs")

        # 2. 하이브리드 검색 (+ 옵션 리랭킹)
        search_results = self.search_engine.search(query, n_results=n_results, hybrid=hybrid, rerank=rerank)
        logger.info(f"Found {len(search_results)} relevant documents")

        # 3. 프롬프트 생성 (Q&A 포함)
        prompt = self.build_prompt(query, search_results, qa_matches)

        # 4. LLM 응답 생성
        answer = self.llm.generate(prompt)

        return RAGResponse(
            answer=answer,
            sources=search_results,
            query=query,
            qa_matches=qa_matches  # Q&A 매칭 결과 추가
        )

    def interactive_mode(self):
        """대화형 모드"""
        print("\n" + "=" * 60)
        print("FCC/ISED 인증 Q&A 시스템")
        print("=" * 60)
        print("질문을 입력하세요. 종료하려면 'exit' 또는 'quit'을 입력하세요.\n")

        while True:
            try:
                query = input("\n질문: ").strip()
                if query.lower() in ['exit', 'quit', '종료']:
                    print("시스템을 종료합니다.")
                    break
                if not query:
                    continue

                response = self.ask(query)

                print("\n" + "-" * 40)
                print("답변:")
                print("-" * 40)
                print(response.answer)

                print("\n" + "-" * 40)
                print("참고 문서:")
                print("-" * 40)
                for i, src in enumerate(response.sources[:3]):
                    print(f"  [{i+1}] {src.doc_id} ({src.source_file})")
                    print(f"      유사도: {1 - src.distance:.2%}")
                    print(f"      내용: {src.content[:100]}...")

            except KeyboardInterrupt:
                print("\n시스템을 종료합니다.")
                break
            except Exception as e:
                print(f"오류 발생: {e}")


def demo():
    """데모 실행"""
    print("=" * 60)
    print("RAG 시스템 데모")
    print("=" * 60)

    # Mock LLM으로 시작 (LLM 없이 검색만)
    rag = RAGSystem(llm_backend=MockLLMBackend())

    test_queries = [
        "DFS 테스트 절차는 무엇인가요?",
        "모듈 인증 요구사항에 대해 설명해주세요",
        "RF 노출 제한은 어떻게 되나요?"
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"질문: {query}")
        print("=" * 60)

        response = rag.ask(query)

        print(f"\n답변: {response.answer}")
        print(f"\n관련 문서 ({len(response.sources)}개):")
        for i, src in enumerate(response.sources[:3]):
            print(f"  [{i+1}] {src.doc_id} (유사도: {1-src.distance:.2%})")
            print(f"      {src.content[:150]}...")


def check_ollama():
    """Ollama 상태 확인"""
    import requests

    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("Ollama 사용 가능!")
            print(f"설치된 모델: {[m['name'] for m in models]}")
            return True
    except:
        pass

    print("Ollama가 실행되고 있지 않습니다.")
    print("설치: https://ollama.ai")
    print("실행: ollama serve")
    print("모델 다운로드: ollama pull llama3")
    return False


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--check':
        check_ollama()
    elif len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        # Ollama 확인 후 대화형 모드
        if check_ollama():
            rag = RAGSystem(llm_backend=OllamaBackend())
        else:
            print("\nMock LLM으로 시작합니다 (검색만 동작)")
            rag = RAGSystem(llm_backend=MockLLMBackend())
        rag.interactive_mode()
    else:
        demo()
