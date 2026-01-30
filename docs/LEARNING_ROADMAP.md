# FCC/ISED 인증 Q&A 시스템 학습 로드맵

## 문서 계층 구조

```
┌─────────────────────────────────────────────────────────────┐
│  eCFR (규제)                                                │
│  "무엇을 만족해야 하는가?"                                    │
│  - 시험 제한치 (출력, 스퓨리어스, 대역폭)                      │
│  - 기본 요구사항                                             │
│  - 적용 주파수 대역                                          │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│  KDB (가이던스)                                              │
│  "어떻게 시험해야 하는가?"                                    │
│  - 시험 절차 (Test Procedure)                                │
│  - 측정 방법 (RBW, Detector 등)                              │
│  - 해석 가이던스                                             │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│  Test Report (실무)                                          │
│  "실제로 어떻게 했는가?"                                      │
│  - 상세 시험 프로시져                                        │
│  - 사용 장비 (Spectrum Analyzer, Signal Generator)           │
│  - 시험 셋업 사진/다이어그램                                  │
│  - 실제 측정 데이터                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: 기반 강화 (현재 ~ 2주)

### 1.1 Q&A 품질 개선
- [ ] 피드백 수집 및 분석
- [ ] 낮은 평점 Q&A 수정/보강
- [ ] 자주 매칭 안 되는 질문 유형 파악

### 1.2 크로스 레퍼런스 Q&A
```
현재: "UNII-1 출력 제한?" → "1W EIRP (§15.407)"

개선: "UNII-1 출력 제한?" →
      - 제한치: 1W EIRP (§15.407)
      - 측정방법: KDB 905462 Section 7
      - 예시: [Test Report에서 실제 측정값]
```

### 1.3 추가 규격 Q&A 생성
- [ ] Bluetooth (KDB 784748) 확장
- [ ] Wi-Fi 6E (6GHz) 강화
- [ ] WWAN (Part 22/24/27) 강화

---

## Phase 2: 실무 데이터 강화 (2주 ~ 1개월)

### 2.1 Test Report 분석 자동화
```python
# Test Report에서 추출할 정보
- 사용 장비 목록 (Manufacturer, Model)
- 시험 셋업 구성
- 측정 파라미터 (RBW, VBW, Detector)
- 실제 측정값 vs 제한치
```

### 2.2 장비 데이터베이스 구축
| 장비 유형 | 용도 | 예시 |
|----------|------|------|
| Spectrum Analyzer | 출력/스퓨리어스 측정 | R&S FSW, Keysight N9040B |
| Signal Generator | DFS 테스트 | R&S SMW200A |
| Power Meter | Conducted Power | Keysight N1912A |
| Antenna | Radiated 측정 | ETS-Lindgren 3115 |

### 2.3 시험 셋업 템플릿
```
[UNII-1 Conducted Power 측정]
1. DUT → 케이블 → Power Meter
2. 설정: Max Power Mode, All Channels
3. 측정: Peak Power per Channel
4. 계산: EIRP = Conducted + Antenna Gain
```

---

## Phase 3: 지능형 답변 (1개월 ~ 2개월)

### 3.1 문맥 기반 답변 분기
```
질문: "UNII-1 출력 제한?"

[기본 모드] → 제한치 + 조항
[상세 모드] → + 측정 방법 + 장비
[실무 모드] → + Test Report 예시 + 주의사항
```

### 3.2 제한치 자동 룩업
```python
def get_limit(band: str, parameter: str) -> dict:
    """
    예: get_limit("UNII-1", "EIRP")
    반환: {
        "value": "1W (30 dBm)",
        "source": "§15.407(a)(1)",
        "measurement": "KDB 905462 Section 7.1"
    }
    """
```

### 3.3 프로시져 체인
```
"UNII-1 테스트 어떻게 해?" →

Step 1: 적용 규격 확인 (eCFR)
        - Part 15 Subpart E 적용
        - 5150-5250 MHz

Step 2: 시험 항목 (KDB 905462)
        - Peak Output Power
        - PSD (Power Spectral Density)
        - 6dB Bandwidth
        - Out-of-band Emissions

Step 3: 측정 방법
        - Conducted: Cable + Power Meter
        - Radiated: Anechoic Chamber + SA

Step 4: 실제 예시 (Test Report)
        - [측정 데이터 예시]
```

---

## Phase 4: 자동화 (2개월+)

### 4.1 Test Report 자동 리뷰
```
[입력] 새 Test Report PDF
[출력]
  - 필수 항목 체크리스트
  - 누락된 측정 항목
  - 제한치 초과 여부
  - 개선 권장사항
```

### 4.2 시험 계획 생성
```
[입력] "Wi-Fi 6E AP, 미국/캐나다 인증"
[출력]
  - 적용 규격 목록
  - 필요 시험 항목
  - 예상 소요 시간
  - 필요 장비 목록
```

### 4.3 규격 변경 모니터링
```
- FCC KDB 업데이트 감지
- eCFR 개정 추적
- 영향받는 Q&A 자동 업데이트
```

---

## 데이터 확장 계획

### 추가 Test Report (권장)
| 기술 | 현재 | 목표 | 우선순위 |
|-----|------|------|---------|
| UNII (5GHz) | 1개 | 3개 | 높음 |
| Wi-Fi 6E (6GHz) | 1개 | 3개 | 높음 |
| Bluetooth | 1개 | 2개 | 중간 |
| UWB | 1개 | 2개 | 중간 |
| WWAN | 1개 | 2개 | 낮음 |

### 추가 KDB
| KDB | 내용 | 우선순위 |
|-----|------|---------|
| KDB 644545 | Modular Approval | 높음 |
| KDB 996369 | 6GHz Rules (확장) | 높음 |
| KDB 484596 | MIMO/Beamforming | 중간 |

---

## 성과 지표

### 정량적 목표
| 지표 | 현재 | 1개월 | 3개월 |
|-----|------|-------|-------|
| Q&A 수 | 413 | 600 | 1000 |
| 매칭률 | ~85% | 90% | 95% |
| 평균 평점 | - | 3.5/5 | 4.0/5 |
| Test Report | 5개 | 10개 | 20개 |

### 정성적 목표
- [ ] "실무자가 바로 쓸 수 있는 답변" 수준
- [ ] 시험 계획 수립 지원 가능
- [ ] Test Report 리뷰 자동화

---

## 즉시 실행 가능한 작업

### 이번 주
1. 피드백 수집 시작 (Streamlit에서 평가)
2. UNII/Wi-Fi 6E Q&A 보강 (가장 많이 쓰는 규격)
3. 장비 정보 추출 스크립트 작성

### 다음 주
1. 피드백 분석 → 낮은 평점 Q&A 개선
2. Test Report 추가 (가능하면)
3. 크로스 레퍼런스 Q&A 시작

---

## 패키지 기반 크로스 레퍼런스 학습 (핵심 전략)

### 개념

Test Report에는 적용된 규격이 모두 나열되어 있음. 이를 활용하여 **패키지 단위**로 연관 문서를 묶어서 크로스 학습.

```
┌─────────────────────────────────────────────────────────────────┐
│                    📦 인증 패키지 구조                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Test Report (중심)                                      │   │
│  │  "이 제품은 이렇게 시험했다"                               │   │
│  │  - 적용 규격 목록 (FCC ID, Part 번호, KDB 번호)           │   │
│  │  - 시험 결과 데이터                                       │   │
│  │  - 사용 장비/셋업                                         │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │                                       │
│         ┌───────────────┼───────────────┐                       │
│         ↓               ↓               ↓                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ eCFR        │ │ KDB         │ │ 연관 자료    │               │
│  │ (규제)      │ │ (가이던스)   │ │ (실무)       │               │
│  │             │ │             │ │             │               │
│  │ Part 15E    │ │ KDB 905462  │ │ 튠업 데이터  │               │
│  │ Part 15C    │ │ KDB 558074  │ │ 안테나 패턴  │               │
│  │ Part 2      │ │ KDB 388624  │ │ SAR 리포트   │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 패키지 정의 예시

```python
# 패키지 구조 정의
CERTIFICATION_PACKAGES = {
    "UNII_5GHz_AP": {
        "name": "UNII 5GHz Access Point",
        "test_reports": [
            "TR_UNII_5GHz_AP_2024.pdf"
        ],
        "ecfr": [
            "Part_15_Subpart_E.pdf",    # UNII 규정
            "Part_2_Subpart_J.pdf"       # 일반 규정
        ],
        "kdb": [
            "KDB_905462.pdf",            # U-NII 시험 절차
            "KDB_558074.pdf",            # WLAN 측정
            "KDB_388624.pdf"             # DFS
        ],
        "related": [
            "Antenna_Pattern_Data.xlsx",
            "Tune_Up_Log.xlsx",
            "Equipment_Cal_Certs.pdf"
        ]
    },
    "WiFi6E_Router": {
        "name": "Wi-Fi 6E Router (6GHz)",
        "test_reports": ["TR_WiFi6E_Router_2024.pdf"],
        "ecfr": ["Part_15_Subpart_E.pdf"],
        "kdb": ["KDB_996369.pdf", "KDB_905462.pdf"],
        "related": ["AFC_Config_Data.json"]
    },
    "Bluetooth_Module": {
        "name": "Bluetooth Classic + LE Module",
        "test_reports": ["TR_BT_Module_2024.pdf"],
        "ecfr": ["Part_15_Subpart_C.pdf"],
        "kdb": ["KDB_784748.pdf", "KDB_248227.pdf"],
        "related": ["BT_Protocol_Log.txt"]
    }
}
```

### 크로스 레퍼런스 Q&A 생성 방식

```
[Step 1] Test Report 분석
         - 적용 규격 목록 추출
         - 시험 항목/결과 추출

[Step 2] 연관 규격 매핑
         - Test Report에서 참조한 eCFR 조항 식별
         - Test Report에서 참조한 KDB 섹션 식별

[Step 3] 크로스 Q&A 생성
         질문: "UNII-1 출력 어떻게 측정해?"

         답변:
         📋 규정 (eCFR §15.407):
            - 제한치: 1W EIRP (30 dBm)
            - 적용 대역: 5150-5250 MHz

         📝 시험 절차 (KDB 905462 Section 7):
            - Peak Power 측정
            - RBW: 1 MHz
            - Detector: Peak

         🔧 실제 예시 (Test Report):
            - 장비: R&S FSW43 Spectrum Analyzer
            - 측정값: 28.5 dBm (Pass)
            - 셋업: DUT → 30dB Attenuator → SA
```

### 구현 단계

#### Phase A: 패키지 정의 (1일)
```
1. 기존 Test Report에서 적용 규격 추출
2. 패키지 JSON 구조 정의
3. 패키지별 문서 매핑
```

#### Phase B: 크로스 레퍼런스 추출 (2-3일)
```
1. Test Report에서 조항 번호 추출 (§15.407, Part 2.1046 등)
2. KDB 섹션 번호 추출 (Section 7.1, 8.2 등)
3. 규격 ↔ 레포트 간 매핑 테이블 생성
```

#### Phase C: 패키지 Q&A 생성 (3-5일)
```
1. 패키지별 종합 Q&A 생성
2. 3방향 연결: eCFR ↔ KDB ↔ Test Report
3. 실제 측정 예시 포함
```

#### Phase D: 검증 및 피드백 (지속)
```
1. 생성된 Q&A 품질 검토
2. 실무자 피드백 반영
3. 누락된 연결 보완
```

### 기대 효과

| 현재 | 패키지 학습 후 |
|------|--------------|
| 단편적 정보 제공 | 종합적 답변 (규정+절차+예시) |
| "제한치가 뭐야?" | "제한치 + 측정법 + 실제 결과" |
| 문서 간 연결 없음 | 3방향 크로스 레퍼런스 |
| 이론 위주 | 실무 데이터 포함 |

### 튠업/연관 자료 활용

```
튠업 데이터 활용 예시:
- "왜 채널 36에서 출력이 가장 높아?"
  → 튠업 로그에서 채널별 출력 차이 확인

- "안테나 게인이 얼마야?"
  → 안테나 패턴 데이터에서 피크 게인 확인

- "SAR 시험 거리는?"
  → SAR 리포트에서 실제 측정 거리 확인
```

### 실행 명령

```bash
# 패키지 기반 Q&A 생성 (예정)
python scripts/generate_package_qa.py --package "UNII_5GHz_AP"

# 전체 패키지 일괄 생성
python scripts/generate_package_qa.py --all

# 특정 Test Report에서 패키지 자동 생성
python scripts/create_package_from_report.py --report "TR_UNII_5GHz.pdf"
```

---

*작성일: 2026-01-31*
*업데이트: 2026-01-31 (패키지 기반 학습 계획 추가)*
*Claude와 함께 계획*
