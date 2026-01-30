# -*- coding: utf-8 -*-
"""
핵심 규격 문서에서 Q&A 쌍 자동 생성
Claude API를 사용하여 Synthetic Q&A 데이터 생성
"""

import json
import sys
import os
import time
import io
from pathlib import Path
from datetime import datetime

# Windows 콘솔 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 경로 설정
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

# ============================================================
# 핵심 규격 정의 (RF 인증에서 자주 사용되는 문서)
# ============================================================

KEY_DOCUMENTS = {
    "kdb": [
        # WLAN / Wi-Fi
        "KDB_905462",      # U-NII (5GHz WLAN) 측정 절차 - 매우 중요
        "KDB_996369",      # 6GHz U-NII 규칙 - 신규 중요
        "KDB_388624",      # DFS 테스트 가이던스
        "KDB_248227",      # 15.247 DTS 가이던스
        "KDB_558074",      # WLAN 측정 관련

        # 기타 무선
        "KDB_393764",      # UWB 가이던스
        "KDB_273109",      # WWAN Part 22/24/27
        "KDB_789033",      # Short-range devices
        "KDB_987594",      # Low power 무선
    ],
    "ecfr": [
        # Part 15 (비인가 기기)
        "CFR_Part_15C",    # 15.247 - Spread Spectrum, DTS
        "CFR_Part_15E",    # U-NII (5GHz, 6GHz WLAN)

        # 이동통신
        "CFR_Part_22",     # Cellular
        "CFR_Part_24",     # PCS (주요!)
        "CFR_Part_27",     # Misc Wireless

        # 기타
        "CFR_Part_2",      # 일반 규정, RF Exposure
    ],
    "rss": [
        # 핵심 RSS
        "RSS-247",         # Low-power (15.247 대응) - 핵심!
        "RSS-GEN",         # General requirements - 필수

        # 특정 기술
        "RSS-248",         # Digital transmission
        "RSS-199",         # Broadband (WWAN 대응)
        "RSS-220",         # UWB
        "RSS-191",         # LMC systems
    ]
}

# Q&A 생성 프롬프트
QA_GENERATION_PROMPT = """당신은 FCC/ISED RF 인증 시험 전문가입니다.
아래 규격 문서를 읽고, RF 인증 엔지니어가 실무에서 물어볼 만한 질문과 답변을 생성하세요.

## 규격 문서
{document}

## 출처 정보
- 문서 ID: {doc_id}
- 문서 유형: {source_type}

## 생성 규칙
1. 실무에서 자주 묻는 질문 위주로 생성
2. 구체적인 수치, 조건, 측정 방법 관련 질문
3. 답변에는 반드시 근거 조항/섹션 포함
4. 한국어로 작성

## 출력 형식 (JSON)
```json
[
  {{
    "question": "UNII-1 대역의 최대 출력 제한은?",
    "answer": "UNII-1 (5.15-5.25 GHz) 대역의 최대 출력은 1W EIRP입니다. 단, 실내 전용으로 제한됩니다. (§ 15.407(a)(1))",
    "category": "출력제한"
  }},
  {{
    "question": "...",
    "answer": "...",
    "category": "..."
  }}
]
```

3-5개의 Q&A를 생성하세요. JSON만 출력하세요.
"""


def get_claude_client():
    """Claude API 클라이언트 생성"""
    try:
        from anthropic import Anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            # .env 파일에서 로드 시도
            env_file = BASE_DIR / ".env"
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith("ANTHROPIC_API_KEY="):
                            api_key = line.split("=", 1)[1].strip().strip('"\'')
                            break

        if not api_key:
            print("❌ ANTHROPIC_API_KEY가 설정되지 않았습니다.")
            print("   환경변수 또는 .env 파일에 설정해주세요.")
            return None

        return Anthropic(api_key=api_key)
    except ImportError:
        print("❌ anthropic 패키지가 설치되지 않았습니다.")
        print("   pip install anthropic")
        return None


def get_key_chunks(collection_name: str, doc_patterns: list, max_per_doc: int = 3):
    """핵심 문서에서 청크 가져오기"""
    import chromadb

    client = chromadb.PersistentClient(path=str(BASE_DIR / "aidata" / "vector_db"))

    # 컬렉션 이름 매핑
    col_map = {
        "kdb": "fcc_kdb",
        "ecfr": "fcc_ecfr",
        "rss": "ised_rss"
    }

    col_name = col_map.get(collection_name)
    if not col_name:
        return []

    try:
        collection = client.get_collection(col_name)
    except:
        print(f"  ⚠️ 컬렉션 {col_name} 없음")
        return []

    # 전체 문서 가져오기
    all_docs = collection.get(include=['documents', 'metadatas'])

    chunks = []
    for pattern in doc_patterns:
        # 패턴에 맞는 문서 필터링
        matched = []
        for i, doc_id in enumerate(all_docs['ids']):
            if pattern.lower() in doc_id.lower():
                matched.append({
                    'id': doc_id,
                    'content': all_docs['documents'][i],
                    'metadata': all_docs['metadatas'][i] if all_docs['metadatas'] else {}
                })

        # 문서당 최대 N개 청크만 선택 (앞부분 위주 - 보통 핵심 내용)
        for chunk in matched[:max_per_doc]:
            chunks.append({
                'doc_id': chunk['id'],
                'content': chunk['content'][:2000],  # 토큰 제한
                'source_type': collection_name,
                'source_file': chunk['metadata'].get('source_file', pattern)
            })

    return chunks


def generate_qa_for_chunk(client, chunk: dict) -> list:
    """단일 청크에서 Q&A 생성"""
    prompt = QA_GENERATION_PROMPT.format(
        document=chunk['content'],
        doc_id=chunk['doc_id'],
        source_type=chunk['source_type'].upper()
    )

    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",  # 비용 효율적인 Haiku 사용
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        # JSON 파싱
        response_text = response.content[0].text

        # JSON 블록 추출
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0]
        else:
            json_str = response_text

        qa_pairs = json.loads(json_str.strip())

        # 출처 정보 추가
        for qa in qa_pairs:
            qa['source_doc_id'] = chunk['doc_id']
            qa['source_type'] = chunk['source_type']
            qa['source_file'] = chunk['source_file']

        return qa_pairs

    except json.JSONDecodeError as e:
        print(f"    ⚠️ JSON 파싱 실패: {e}")
        return []
    except Exception as e:
        print(f"    ⚠️ API 오류: {e}")
        return []


def main():
    print("=" * 60)
    print("Q&A 쌍 자동 생성 (핵심 규격 문서)")
    print("=" * 60)

    # Claude 클라이언트
    client = get_claude_client()
    if not client:
        return

    all_qa_pairs = []
    total_chunks = 0

    # 각 컬렉션별 처리
    for source_type, doc_patterns in KEY_DOCUMENTS.items():
        print(f"\n📁 {source_type.upper()} 문서 처리 중...")

        chunks = get_key_chunks(source_type, doc_patterns, max_per_doc=2)
        print(f"   {len(chunks)}개 청크 선택됨")

        for i, chunk in enumerate(chunks):
            print(f"   [{i+1}/{len(chunks)}] {chunk['doc_id'][:40]}...", end=" ")

            qa_pairs = generate_qa_for_chunk(client, chunk)

            if qa_pairs:
                all_qa_pairs.extend(qa_pairs)
                print(f"✓ {len(qa_pairs)}개 Q&A 생성")
            else:
                print("✗ 실패")

            total_chunks += 1

            # Rate limit 방지
            time.sleep(0.5)

    # 결과 저장
    output_file = BASE_DIR / "aidata" / "qa_pairs.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "generated_at": datetime.now().isoformat(),
        "total_qa_pairs": len(all_qa_pairs),
        "source_chunks": total_chunks,
        "qa_pairs": all_qa_pairs
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"✅ 완료!")
    print(f"   - 처리된 청크: {total_chunks}개")
    print(f"   - 생성된 Q&A: {len(all_qa_pairs)}개")
    print(f"   - 저장 위치: {output_file}")
    print("=" * 60)

    # 샘플 출력
    if all_qa_pairs:
        print("\n📝 샘플 Q&A:")
        for qa in all_qa_pairs[:3]:
            print(f"\nQ: {qa['question']}")
            print(f"A: {qa['answer'][:100]}...")


if __name__ == "__main__":
    main()
