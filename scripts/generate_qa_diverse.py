# -*- coding: utf-8 -*-
"""
Q&A 다양화 + 추가 생성
기존 Q&A의 질문을 다양한 표현으로 확장하고, 추가 규격에서 새 Q&A 생성
"""

import json
import sys
import io
import os
import time
from pathlib import Path
from datetime import datetime

# Windows 콘솔 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent.parent

# ============================================================
# 추가 규격 (2단계 확장)
# ============================================================

ADDITIONAL_DOCUMENTS = {
    "kdb": [
        # RF Exposure (다시 추가)
        "KDB_935210",      # RF Exposure 일반
        "KDB_447498",      # RF Exposure KDB
        "KDB_648474",      # SAR 측정

        # 추가 KDB
        "KDB_784748",      # Bluetooth
        "KDB_941225",      # Power measurement
    ],
    "ecfr": [
        # 추가 Part
        "CFR_Part_15B",    # Unintentional radiators
        "CFR_Part_18",     # ISM equipment
        "CFR_Part_15D",    # Unlicensed PCS
    ],
    "rss": [
        # RF Exposure (다시 추가)
        "RSS-102",         # RF Exposure

        # 추가 RSS
        "RSS-210",         # License-exempt (legacy)
        "RSS-310",         # License-exempt (newer)
    ]
}

# 질문 다양화 프롬프트
DIVERSIFY_PROMPT = """기존 Q&A를 기반으로 같은 내용을 묻는 **다른 표현의 질문**을 생성하세요.

## 기존 Q&A
Q: {question}
A: {answer}

## 생성 규칙
1. 같은 답변이 나오는 다른 질문 표현 3개 생성
2. 한국어 1개, 영어 1개, 간략한 표현 1개
3. 실무자가 실제로 물어볼 만한 자연스러운 표현

## 출력 형식 (JSON)
```json
[
  {{"question": "한국어 다른 표현", "lang": "ko"}},
  {{"question": "English version of the question", "lang": "en"}},
  {{"question": "간략한 표현 (예: UNII-1 출력?)", "lang": "short"}}
]
```

JSON만 출력하세요.
"""

# 새 Q&A 생성 프롬프트
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
    "question": "질문 내용",
    "answer": "답변 내용 (조항 번호 포함)",
    "category": "카테고리"
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
            env_file = BASE_DIR / ".env"
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith("ANTHROPIC_API_KEY="):
                            api_key = line.split("=", 1)[1].strip().strip('"\'')
                            break

        if not api_key:
            print("❌ ANTHROPIC_API_KEY가 설정되지 않았습니다.")
            return None

        return Anthropic(api_key=api_key)
    except ImportError:
        print("❌ anthropic 패키지가 설치되지 않았습니다.")
        return None


def load_existing_qa():
    """기존 Q&A 로드"""
    qa_file = BASE_DIR / "aidata" / "qa_pairs.json"
    if qa_file.exists():
        with open(qa_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('qa_pairs', [])
    return []


def diversify_questions(client, qa_pairs, max_items=50):
    """기존 Q&A의 질문을 다양화"""
    print("\n📝 질문 다양화 중...")

    diversified = []

    # 상위 N개 Q&A만 다양화 (비용 절감)
    for i, qa in enumerate(qa_pairs[:max_items]):
        print(f"   [{i+1}/{min(len(qa_pairs), max_items)}] {qa['question'][:30]}...", end=" ")

        prompt = DIVERSIFY_PROMPT.format(
            question=qa['question'],
            answer=qa['answer']
        )

        try:
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # JSON 파싱
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            else:
                json_str = response_text

            new_questions = json.loads(json_str.strip())

            # 새 질문들 추가 (같은 답변 공유)
            for new_q in new_questions:
                diversified.append({
                    'question': new_q['question'],
                    'answer': qa['answer'],
                    'category': qa.get('category', '') + f"_{new_q.get('lang', 'var')}",
                    'source_doc_id': qa.get('source_doc_id', ''),
                    'source_type': qa.get('source_type', ''),
                    'source_file': qa.get('source_file', ''),
                    'is_diversified': True,
                    'original_question': qa['question']
                })

            print(f"✓ +{len(new_questions)}개")

        except Exception as e:
            print(f"✗ {e}")

        time.sleep(0.3)

    return diversified


def get_key_chunks(collection_name: str, doc_patterns: list, max_per_doc: int = 2):
    """핵심 문서에서 청크 가져오기"""
    import chromadb

    client = chromadb.PersistentClient(path=str(BASE_DIR / "aidata" / "vector_db"))

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
        return []

    all_docs = collection.get(include=['documents', 'metadatas'])

    chunks = []
    for pattern in doc_patterns:
        matched = []
        for i, doc_id in enumerate(all_docs['ids']):
            if pattern.lower() in doc_id.lower():
                matched.append({
                    'id': doc_id,
                    'content': all_docs['documents'][i],
                    'metadata': all_docs['metadatas'][i] if all_docs['metadatas'] else {}
                })

        for chunk in matched[:max_per_doc]:
            chunks.append({
                'doc_id': chunk['id'],
                'content': chunk['content'][:2000],
                'source_type': collection_name,
                'source_file': chunk['metadata'].get('source_file', pattern)
            })

    return chunks


def generate_new_qa(client, chunks):
    """새 문서에서 Q&A 생성"""
    print("\n📄 추가 문서에서 Q&A 생성 중...")

    new_qa = []

    for i, chunk in enumerate(chunks):
        print(f"   [{i+1}/{len(chunks)}] {chunk['doc_id'][:40]}...", end=" ")

        prompt = QA_GENERATION_PROMPT.format(
            document=chunk['content'],
            doc_id=chunk['doc_id'],
            source_type=chunk['source_type'].upper()
        )

        try:
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            else:
                json_str = response_text

            qa_pairs = json.loads(json_str.strip())

            for qa in qa_pairs:
                qa['source_doc_id'] = chunk['doc_id']
                qa['source_type'] = chunk['source_type']
                qa['source_file'] = chunk['source_file']

            new_qa.extend(qa_pairs)
            print(f"✓ {len(qa_pairs)}개")

        except Exception as e:
            print(f"✗ {e}")

        time.sleep(0.5)

    return new_qa


def main():
    print("=" * 60)
    print("Q&A 다양화 + 확장 (목표: 420개)")
    print("=" * 60)

    client = get_claude_client()
    if not client:
        return

    # 1. 기존 Q&A 로드
    existing_qa = load_existing_qa()
    print(f"\n📊 기존 Q&A: {len(existing_qa)}개")

    # 2. 질문 다양화 (기존 Q&A의 50개를 다양화 → +150개 예상)
    diversified_qa = diversify_questions(client, existing_qa, max_items=50)
    print(f"   → 다양화된 Q&A: +{len(diversified_qa)}개")

    # 3. 추가 문서에서 새 Q&A 생성
    all_new_qa = []
    for source_type, doc_patterns in ADDITIONAL_DOCUMENTS.items():
        print(f"\n📁 {source_type.upper()} 추가 문서...")
        chunks = get_key_chunks(source_type, doc_patterns, max_per_doc=2)
        print(f"   {len(chunks)}개 청크")

        new_qa = generate_new_qa(client, chunks)
        all_new_qa.extend(new_qa)

    print(f"\n   → 새 Q&A: +{len(all_new_qa)}개")

    # 4. 전체 병합
    final_qa = existing_qa + diversified_qa + all_new_qa

    # 5. 저장
    output_file = BASE_DIR / "aidata" / "qa_pairs.json"
    output_data = {
        "generated_at": datetime.now().isoformat(),
        "total_qa_pairs": len(final_qa),
        "breakdown": {
            "original": len(existing_qa),
            "diversified": len(diversified_qa),
            "new_documents": len(all_new_qa)
        },
        "qa_pairs": final_qa
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"✅ 완료!")
    print(f"   - 기존 Q&A: {len(existing_qa)}개")
    print(f"   - 다양화: +{len(diversified_qa)}개")
    print(f"   - 새 문서: +{len(all_new_qa)}개")
    print(f"   - 총합: {len(final_qa)}개")
    print(f"   - 저장: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
