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

*작성일: 2026-01-31*
*Claude와 함께 계획*
