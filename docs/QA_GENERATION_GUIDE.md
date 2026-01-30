# Q&A 쌍 자동 생성 가이드

> **현재 상태**: 413개 Q&A (2026-01-31 기준)
> - 기존 140개 + 다양화 198개 + 추가 문서 75개

## 개요

이 시스템은 규격 문서에서 **Synthetic Q&A (합성 질문-답변)** 데이터를 자동 생성합니다.
Claude API를 사용하여 문서 내용을 분석하고, 실무에서 자주 묻는 질문과 답변을 생성합니다.

### 왜 필요한가?

```
기존 RAG 방식:
  사용자 질문 → 문서 검색 → 문서 내용 기반 답변 생성

  문제점:
  - "출력 제한이 뭐야?" → 문서에 "출력 제한"이라는 단어가 없으면 검색 실패
  - 매번 LLM이 답변 생성 → 일관성 부족, 할루시네이션 위험

Q&A 방식:
  사용자 질문 → Q&A 매칭 → 검증된 답변 제공

  장점:
  - 질문 의도 파악 (질문↔질문 매칭)
  - 미리 검증된 답변 → 품질 일관성
  - LLM 호출 없이 빠른 응답 가능
```

## 시스템 구조

```
┌─────────────────────────────────────────────────────────┐
│                    Q&A 생성 파이프라인                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. 핵심 문서 선택                                       │
│     └── KEY_DOCUMENTS 딕셔너리에 정의                    │
│                                                         │
│  2. 청크 추출                                           │
│     └── 각 문서에서 2-3개 핵심 청크 선택                  │
│                                                         │
│  3. Q&A 생성 (Claude API)                               │
│     └── 청크당 3-5개 Q&A 쌍 생성                         │
│                                                         │
│  4. 저장                                                │
│     └── aidata/qa_pairs.json                           │
│                                                         │
│  5. 검색 시 활용                                         │
│     └── 문서 검색 + Q&A 매칭 병행                        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 사용 방법

### 1. 기본 실행

```bash
cd "C:\Users\younh\Documents\Ai model"
python scripts/generate_qa_pairs.py
```

### 2. API 키 설정

환경변수 또는 `.env` 파일에 설정:

```bash
# 환경변수
set ANTHROPIC_API_KEY=sk-ant-xxxxx

# 또는 .env 파일
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

### 3. 출력 파일

- **위치**: `aidata/qa_pairs.json`
- **형식**:
```json
{
  "generated_at": "2026-01-31T00:00:00",
  "total_qa_pairs": 150,
  "source_chunks": 50,
  "qa_pairs": [
    {
      "question": "UNII-1 대역의 최대 출력 제한은?",
      "answer": "UNII-1 (5.15-5.25 GHz) 대역의 최대 출력은 1W EIRP입니다...",
      "category": "출력제한",
      "source_doc_id": "KDB_905462_chunk_001",
      "source_type": "kdb",
      "source_file": "KDB_905462.pdf"
    }
  ]
}
```

## 규격 추가/삭제 방법

### 파일 위치
`scripts/generate_qa_pairs.py` 의 `KEY_DOCUMENTS` 딕셔너리

### 현재 등록된 규격

```python
KEY_DOCUMENTS = {
    "kdb": [
        "KDB_905462",      # U-NII (5GHz WLAN)
        "KDB_996369",      # 6GHz U-NII
        "KDB_388624",      # DFS
        "KDB_248227",      # 15.247 DTS
        "KDB_558074",      # WLAN 측정
        "KDB_393764",      # UWB
        "KDB_273109",      # WWAN
        "KDB_789033",      # Short-range
        "KDB_987594",      # Low power
    ],
    "ecfr": [
        "CFR_Part_15C",    # 15.247 Spread Spectrum
        "CFR_Part_15E",    # U-NII
        "CFR_Part_22",     # Cellular
        "CFR_Part_24",     # PCS
        "CFR_Part_27",     # Misc Wireless
        "CFR_Part_2",      # 일반 규정
    ],
    "rss": [
        "RSS-247",         # Low-power
        "RSS-GEN",         # General
        "RSS-248",         # Digital transmission
        "RSS-199",         # Broadband
        "RSS-220",         # UWB
        "RSS-191",         # LMC
    ]
}
```

### 규격 추가하기

1. **스크립트 수정**:
```python
# KDB 추가 예시
"kdb": [
    ...기존 목록...,
    "KDB_123456",      # 새 KDB 설명
],

# eCFR 추가 예시
"ecfr": [
    ...기존 목록...,
    "CFR_Part_15B",    # Part 15 Subpart B
],

# RSS 추가 예시
"rss": [
    ...기존 목록...,
    "RSS-210",         # License-exempt 구형
],
```

2. **실행**:
```bash
python scripts/generate_qa_pairs.py
```

3. **결과 확인**:
   - `aidata/qa_pairs.json` 파일 확인
   - 새로 추가된 Q&A 검토

### 규격 삭제하기

해당 라인을 주석처리하거나 삭제:
```python
"kdb": [
    "KDB_905462",
    # "KDB_996369",  # 주석처리로 제외
    "KDB_388624",
],
```

### 문서명 찾는 방법

벡터DB에 저장된 문서명 확인:
```python
import chromadb
client = chromadb.PersistentClient(path="aidata/vector_db")

# KDB 목록
col = client.get_collection("fcc_kdb")
ids = col.get()['ids']
unique_docs = set(id.rsplit('_', 1)[0] for id in ids)
print(sorted(unique_docs))

# eCFR 목록
col = client.get_collection("fcc_ecfr")
# ... 동일
```

## 비용 관리

### 예상 비용 (Claude Haiku 기준)

| 규모 | 청크 수 | 예상 비용 |
|-----|--------|----------|
| 소규모 | ~30개 | ~$0.5 |
| 중규모 | ~50개 | ~$1-1.5 |
| 대규모 | ~100개 | ~$2-3 |

### 비용 절감 팁

1. **핵심 문서만 선택**: 자주 사용하는 규격 위주
2. **청크 수 제한**: `max_per_doc` 파라미터 조정
3. **점진적 추가**: 한 번에 모두 하지 말고 필요할 때마다 추가

## 품질 관리

### 생성된 Q&A 검토

1. `aidata/qa_pairs.json` 파일 열기
2. 각 Q&A의 정확성 확인
3. 부정확한 Q&A 수정 또는 삭제

### 피드백 기반 개선

1. 사용자 피드백 수집 (`aidata/feedback.json`)
2. 낮은 평점 받은 질문 유형 파악
3. 해당 유형 문서에서 Q&A 재생성 또는 수동 추가

### 수동 Q&A 추가

`qa_pairs.json`에 직접 추가 가능:
```json
{
  "question": "직접 작성한 질문",
  "answer": "직접 작성한 답변",
  "category": "카테고리",
  "source_doc_id": "manual",
  "source_type": "manual",
  "source_file": "수동 입력"
}
```

## 다음 단계

### 1단계: Q&A 생성 (현재)
- 핵심 규격에서 자동 생성
- 품질 검토 및 수정

### 2단계: Q&A 벡터DB 저장
- 생성된 Q&A를 별도 컬렉션에 저장
- 질문을 임베딩하여 검색 가능하게

### 3단계: 하이브리드 검색
- 기존 문서 검색 + Q&A 매칭 병행
- Q&A 매칭 시 검증된 답변 우선 제공

### 4단계: 지속적 개선
- 피드백 기반 Q&A 추가/수정
- 새 규격 추가 시 Q&A 생성

## 🚀 Claude에게 요청하는 방법

### 규격 추가 요청
```
"KDB 123456 추가해줘"
"Part 15B 규격 Q&A 생성해줘"
"RSS-102 RF Exposure 추가해줘"
```

### Q&A 수량 증가 요청
```
"Q&A 100개 더 만들어줘"
"DFS 관련 질문 다양화해줘"
"영어 질문 버전도 추가해줘"
```

### 특정 주제 강화 요청
```
"UNII 출력 관련 Q&A 보강해줘"
"SAR 측정 관련 질문 추가해줘"
"Bluetooth 인증 Q&A 더 만들어줘"
```

### 품질 개선 요청
```
"매칭 안 되는 질문들 확인해줘"
"피드백 낮은 Q&A 개선해줘"
```

## 스크립트 목록

| 스크립트 | 용도 | 실행 방법 |
|---------|------|----------|
| `generate_qa_pairs.py` | 기본 Q&A 생성 | `python scripts/generate_qa_pairs.py` |
| `generate_qa_diverse.py` | 질문 다양화 + 확장 | `python scripts/generate_qa_diverse.py` |
| `generate_qa_more.py` | 추가 다양화 | `python scripts/generate_qa_more.py` |
| `add_qa_to_vectordb.py` | 벡터DB 저장 | `python scripts/add_qa_to_vectordb.py` |

## 작업 흐름

```
1. Q&A 생성/추가
   ↓
2. aidata/qa_pairs.json 저장
   ↓
3. add_qa_to_vectordb.py 실행 (벡터DB 업데이트)
   ↓
4. Streamlit 재시작 (변경 적용)
```

## 트러블슈팅

### API 키 오류
```
❌ ANTHROPIC_API_KEY가 설정되지 않았습니다.
```
→ `.env` 파일에 `ANTHROPIC_API_KEY=sk-ant-...` 확인

### JSON 파싱 실패
```
⚠️ JSON 파싱 실패
```
→ LLM 응답 형식 문제, 재시도하면 대부분 해결

### 문서를 찾을 수 없음
```
0개 청크 선택됨
```
→ 벡터DB에 해당 문서가 있는지 확인:
```python
import chromadb
client = chromadb.PersistentClient(path="aidata/vector_db")
col = client.get_collection("fcc_kdb")  # 또는 fcc_ecfr, ised_rss
ids = set(id.split('_')[0] + '_' + id.split('_')[1] for id in col.get()['ids'])
print(sorted(ids))
```

### 벡터DB HNSW 오류
```
Error creating hnsw segment
```
→ 동시 접근 문제. Streamlit 종료 후 스크립트 실행

---

## 현재 Q&A 구성

| 출처 | 개수 | 설명 |
|-----|-----|------|
| 기존 | 140개 | 핵심 규격 기본 Q&A |
| 다양화 | ~200개 | 한국어/영어/짧은 표현 |
| 추가 문서 | ~75개 | RF Exposure, Part 15B, 18 등 |
| **총합** | **413개** | |

---

*마지막 업데이트: 2026-01-31*
