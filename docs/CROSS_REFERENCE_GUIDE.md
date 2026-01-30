# 크로스 레퍼런스 Q&A 생성 가이드

> **목적:** 규격 전체와 레포트를 수직 크로스하여 종합 Q&A 생성

---

## 전체 워크플로우

```
┌─────────────────────────────────────────────────────────────────┐
│                    크로스 레퍼런스 Q&A 생성 프로세스              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: 패키지 정의                                            │
│  ├── 레포트 선택                                                │
│  ├── 관련 규격 (eCFR) 목록                                      │
│  ├── 관련 KDB 목록                                              │
│  └── 관련 표준 목록                                             │
│                                                                 │
│  Step 2: 텍스트 추출                                            │
│  ├── PDF → 텍스트 변환 (필요시)                                 │
│  └── 텍스트 파일 확인                                           │
│                                                                 │
│  Step 3: Phase 1 - 개별 Q&A 생성                                │
│  ├── 각 규격별 자체 Q&A                                         │
│  └── 레포트 자체 Q&A                                            │
│                                                                 │
│  Step 4: Phase 3 - 수직 크로스 Q&A                              │
│  ├── 전체 규격 + 레포트 입력                                    │
│  └── 종합 Q&A 생성                                              │
│                                                                 │
│  Step 5: 벡터DB 저장                                            │
│  └── 생성된 Q&A를 벡터DB에 추가                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step 1: 패키지 정의

### 패키지 구조 템플릿

```python
# packages/unii_6e_wlan.json
{
    "package_id": "UNII_6E_WLAN_001",
    "package_name": "UNII 6E WLAN Package",
    "created_at": "2026-01-31",

    "report": {
        "file": "AIdata/Testreport/S-4791615583-E11V1 FCC Report UNII(6E) WLAN.pdf",
        "text_file": "AIdata/Testreport/S-4791615583-E11V1.txt",
        "type": "UNII 6GHz WLAN"
    },

    "test_limits": {
        "ecfr": [
            {
                "name": "Part 2",
                "file": "AIdata/raw_data/ecfr/CFR_Part_2.txt",
                "status": "ready"
            },
            {
                "name": "Part 15E",
                "file": "AIdata/raw_data/ecfr/CFR_Part_15E.txt",
                "status": "ready"
            }
        ]
    },

    "test_methods": {
        "kdb": [
            {
                "name": "KDB 789033",
                "description": "General UNII Test Procedures",
                "file": "AIdata/raw_data/kdb/KDB_789033/KDB_789033_D02_General UNII Test Procedures New Rules_v02r01.pdf",
                "text_file": "AIdata/raw_data/kdb/KDB_789033/KDB_789033_D02.txt",
                "status": "need_extraction"
            },
            {
                "name": "KDB 987594",
                "description": "U-NII 6GHz Requirements",
                "files": [
                    "KDB_987594_D01_U-NII 6GHz General Requirements_v03.pdf",
                    "KDB_987594_D02_U-NII 6 GHz EMC Measurement_v03.pdf",
                    "KDB_987594_D03_U-NII 6 GHz QA_v03.pdf",
                    "KDB_987594_D04_UN6GHZ Pre-Approval Guidance Checklist_v03.pdf"
                ],
                "status": "need_extraction"
            },
            {
                "name": "KDB 662911",
                "description": "Multiple Transmitter / MIMO",
                "files": [
                    "KDB_662911_D01_Multiple Transmitter Output_v02r01.pdf",
                    "KDB_662911_D02_MIMO with Cross Polarized Antenna_v01.pdf",
                    "KDB_662911_D03_MIMO Antenna Gain Measurement_v01.pdf"
                ],
                "status": "need_extraction"
            }
        ],
        "standards": [
            {
                "name": "ANSI C63.10-2020",
                "file": "AIdata/global/ANSI c63.10 2020.pdf",
                "text_file": "AIdata/global/ANSI_C63.10_2020.txt",
                "status": "need_extraction"
            }
        ]
    }
}
```

---

## Step 2: 텍스트 추출

### PDF 텍스트 추출 스크립트

```bash
python scripts/extract_pdf_text.py --package packages/unii_6e_wlan.json
```

### 추출 확인

```bash
python scripts/check_package_files.py --package packages/unii_6e_wlan.json
```

---

## Step 3: Phase 1 - 개별 Q&A 생성

### 규격별 자체 Q&A

```bash
# 각 규격에서 자체 Q&A 생성
python scripts/generate_qa_pairs.py --source "Part_2"
python scripts/generate_qa_pairs.py --source "Part_15E"
python scripts/generate_qa_pairs.py --source "KDB_789033"
python scripts/generate_qa_pairs.py --source "KDB_987594"
python scripts/generate_qa_pairs.py --source "KDB_662911"
python scripts/generate_qa_pairs.py --source "ANSI_C63.10"
```

### 레포트 자체 Q&A

```bash
python scripts/generate_qa_pairs.py --source "Report_E11V1"
```

---

## Step 4: Phase 3 - 수직 크로스 Q&A (핵심)

### 전체 규격 + 레포트 크로스

```bash
python scripts/generate_cross_qa.py --package packages/unii_6e_wlan.json
```

### 크로스 Q&A 생성 프롬프트

```python
CROSS_QA_PROMPT = """
당신은 FCC RF 인증 시험 전문가입니다.
아래 규격들과 실제 시험 레포트를 분석하여, 규격과 실무를 연결하는 종합 Q&A를 생성하세요.

## 규격 문서들

### Part 2 (일반 규정)
{part_2_content}

### Part 15E (UNII)
{part_15e_content}

### KDB 789033 (UNII 시험 절차)
{kdb_789033_content}

### KDB 987594 (6GHz 요구사항)
{kdb_987594_content}

### KDB 662911 (MIMO/다중송신)
{kdb_662911_content}

### ANSI C63.10-2020 (측정 표준)
{ansi_c63_10_content}

## 실제 시험 레포트
{report_content}

## 생성 규칙

1. 규격의 요구사항과 레포트의 실제 시험을 연결
2. 각 답변에 다음 포함:
   - 📋 규격 요구사항 (조항 번호)
   - 📝 시험 절차 (KDB 섹션)
   - 📘 측정 표준 (ANSI 조항)
   - 🔧 실제 시험 (레포트 데이터)
   - ⚠️ 실무 팁

3. 포커스 영역:
   - 제한치 vs 실측값
   - 절차 vs 실제 수행
   - 장비/셋업
   - 주의사항

## 출력 형식 (JSON)

```json
[
  {
    "question": "질문",
    "answer": "종합 답변 (규격+절차+실제)",
    "category": "카테고리",
    "cross_references": {
      "ecfr": ["§15.407(a)"],
      "kdb": ["KDB 987594 Section 5"],
      "standard": ["ANSI C63.10 Section 8"],
      "report": ["Section 4.2"]
    }
  }
]
```

20-30개의 종합 Q&A를 생성하세요.
"""
```

### 포커스별 추가 생성

```bash
# 제한치 vs 실측 포커스
python scripts/generate_cross_qa.py --package packages/unii_6e_wlan.json --focus limits

# 절차 vs 실제 포커스
python scripts/generate_cross_qa.py --package packages/unii_6e_wlan.json --focus procedures

# 장비/셋업 포커스
python scripts/generate_cross_qa.py --package packages/unii_6e_wlan.json --focus equipment

# 실무 팁 포커스
python scripts/generate_cross_qa.py --package packages/unii_6e_wlan.json --focus tips
```

---

## Step 5: 벡터DB 저장

```bash
python scripts/add_qa_to_vectordb.py
```

---

## 예상 결과

### Q&A 예시

```
Q: "UNII-5 출력 시험 어떻게 해?"

A: 📋 규격 요구사항 (Part 15E §15.407)
   - UNII-5 (5.925-6.425 GHz): 1W EIRP (indoor)
   - PSD: 5 dBm/MHz

   📝 시험 절차 (KDB 987594 Section 5)
   - LPI 모드 확인
   - AFC 연동 상태 확인
   - Peak Power + PSD 측정

   📝 UNII 공통 (KDB 789033)
   - 모든 채널, 최대 출력 모드
   - 안테나 게인 포함 EIRP 계산

   📝 MIMO 고려 (KDB 662911)
   - 다중 안테나 시 합산 출력 확인

   📘 측정 표준 (ANSI C63.10 Section 8)
   - RBW: 1 MHz
   - Detector: Peak
   - 측정 거리: 3m

   🔧 실제 시험 (레포트 E11V1)
   - 장비: R&S FSW43
   - 측정값: 28.2 dBm (EIRP)
   - 마진: 1.8 dB

   ⚠️ 실무 팁
   - 채널 37 (6135 MHz) 부근 출력 최대
   - AFC 비활성 시 LPI 모드 필수 확인
   - 안테나 게인 측정 불확도 고려
```

---

## 새 패키지 추가 방법

### 1. 패키지 JSON 생성

```bash
# 템플릿 복사
cp packages/unii_6e_wlan.json packages/new_package.json

# 편집
- report 경로 수정
- 관련 규격 목록 수정
- 관련 KDB 목록 수정
```

### 2. 텍스트 추출

```bash
python scripts/extract_pdf_text.py --package packages/new_package.json
```

### 3. Q&A 생성

```bash
# 개별 Q&A
python scripts/generate_qa_pairs.py --package packages/new_package.json

# 크로스 Q&A
python scripts/generate_cross_qa.py --package packages/new_package.json
```

### 4. 벡터DB 업데이트

```bash
python scripts/add_qa_to_vectordb.py
```

---

## 파일 구조

```
Ai model/
├── packages/                      # 패키지 정의
│   ├── unii_6e_wlan.json
│   ├── bluetooth_module.json
│   └── uwb_device.json
│
├── scripts/
│   ├── extract_pdf_text.py       # PDF 텍스트 추출
│   ├── check_package_files.py    # 파일 상태 확인
│   ├── generate_qa_pairs.py      # 개별 Q&A 생성
│   ├── generate_cross_qa.py      # 크로스 Q&A 생성
│   └── add_qa_to_vectordb.py     # 벡터DB 저장
│
├── AIdata/
│   ├── raw_data/
│   │   ├── ecfr/                 # eCFR 텍스트
│   │   ├── kdb/                  # KDB 문서
│   │   └── rss/                  # RSS 문서
│   ├── Testreport/               # 시험 레포트
│   ├── global/                   # 국제 표준
│   └── qa_pairs.json             # 생성된 Q&A
│
└── docs/
    ├── LEARNING_ROADMAP.md       # 학습 로드맵
    ├── QA_GENERATION_GUIDE.md    # Q&A 생성 가이드
    └── CROSS_REFERENCE_GUIDE.md  # 이 문서
```

---

## 체크리스트

### 새 패키지 생성 시

- [ ] 레포트 PDF 준비
- [ ] 관련 규격 (eCFR) 확인
- [ ] 관련 KDB 확인
- [ ] 관련 표준 확인
- [ ] 패키지 JSON 생성
- [ ] PDF 텍스트 추출
- [ ] 개별 Q&A 생성
- [ ] 크로스 Q&A 생성
- [ ] 벡터DB 업데이트
- [ ] 품질 검토

---

## 현재 패키지 상태

### UNII_6E_WLAN_001

| 항목 | 상태 |
|------|------|
| 레포트 | ⬚ 텍스트 추출 필요 |
| Part 2 | ✅ 준비 완료 |
| Part 15E | ✅ 준비 완료 |
| KDB 789033 | ⬚ 텍스트 추출 필요 |
| KDB 987594 | ⬚ 텍스트 추출 필요 |
| KDB 662911 | ⬚ 텍스트 추출 필요 |
| ANSI C63.10 | ⬚ 텍스트 추출 필요 |
| 개별 Q&A | ⬚ 예정 |
| 크로스 Q&A | ⬚ 예정 |

---

*작성일: 2026-01-31*
*Claude와 함께 작성*
