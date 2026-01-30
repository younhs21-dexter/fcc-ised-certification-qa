# -*- coding: utf-8 -*-
"""크로스 레퍼런스 Q&A 생성 스크립트"""

import json
import sys
import io
import os
import time
import re
from pathlib import Path
from datetime import datetime

# Windows 콘솔 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent.parent


def get_claude_client():
    """Claude API 클라이언트 생성"""
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


def extract_key_section(text: str, start_pattern: str, end_pattern: str = None, max_chars: int = 30000) -> str:
    """텍스트에서 핵심 섹션 추출"""
    # 시작 패턴 찾기
    start_match = re.search(start_pattern, text, re.IGNORECASE)
    if not start_match:
        # 패턴 못 찾으면 앞부분 반환
        return text[:max_chars]

    start_pos = start_match.start()

    if end_pattern:
        end_match = re.search(end_pattern, text[start_pos:], re.IGNORECASE)
        if end_match:
            end_pos = start_pos + end_match.end()
            return text[start_pos:end_pos][:max_chars]

    return text[start_pos:start_pos + max_chars]


def load_key_sections():
    """각 문서에서 핵심 섹션 로드"""
    sections = {}

    print("\n📂 핵심 섹션 로드 중...")

    # Part 2 - RF 측정 관련 섹션
    part2_path = BASE_DIR / "AIdata/raw_data/ecfr/CFR_Part_2.txt"
    if part2_path.exists():
        with open(part2_path, 'r', encoding='utf-8') as f:
            text = f.read()
        # §2.1046 ~ §2.1060 (RF 측정 관련)
        sections['part_2'] = extract_key_section(text, r'§\s*2\.1046|2\.1046', max_chars=40000)
        print(f"  ✅ Part 2: {len(sections['part_2']):,}자")

    # Part 15E - UNII 규정
    part15e_path = BASE_DIR / "AIdata/raw_data/ecfr/CFR_Part_15E.txt"
    if part15e_path.exists():
        with open(part15e_path, 'r', encoding='utf-8') as f:
            sections['part_15e'] = f.read()[:50000]
        print(f"  ✅ Part 15E: {len(sections['part_15e']):,}자")

    # KDB 789033 - UNII 시험 절차
    kdb789_path = BASE_DIR / "AIdata/raw_data/kdb/KDB_789033/KDB_789033_D02.txt"
    if kdb789_path.exists():
        with open(kdb789_path, 'r', encoding='utf-8') as f:
            sections['kdb_789033'] = f.read()
        print(f"  ✅ KDB 789033: {len(sections['kdb_789033']):,}자")

    # KDB 987594 - 6GHz (D01 + D02 핵심)
    kdb987_d01 = BASE_DIR / "AIdata/raw_data/kdb/KDB_987594/KDB_987594_D01.txt"
    kdb987_d02 = BASE_DIR / "AIdata/raw_data/kdb/KDB_987594/KDB_987594_D02.txt"
    kdb987_text = ""
    if kdb987_d01.exists():
        with open(kdb987_d01, 'r', encoding='utf-8') as f:
            kdb987_text += f.read()[:50000]
    if kdb987_d02.exists():
        with open(kdb987_d02, 'r', encoding='utf-8') as f:
            kdb987_text += "\n\n" + f.read()[:30000]
    sections['kdb_987594'] = kdb987_text
    print(f"  ✅ KDB 987594: {len(sections['kdb_987594']):,}자")

    # KDB 662911 - MIMO/다중송신 (D01 위주)
    kdb662_path = BASE_DIR / "AIdata/raw_data/kdb/KDB_662911/KDB_662911_D01.txt"
    if kdb662_path.exists():
        with open(kdb662_path, 'r', encoding='utf-8') as f:
            sections['kdb_662911'] = f.read()
        print(f"  ✅ KDB 662911: {len(sections['kdb_662911']):,}자")

    # ANSI C63.10 - 핵심 측정 섹션
    ansi_path = BASE_DIR / "AIdata/global/ANSI_C63.10_2020.txt"
    if ansi_path.exists():
        with open(ansi_path, 'r', encoding='utf-8') as f:
            text = f.read()
        # 측정 관련 섹션 추출
        sections['ansi_c63_10'] = extract_key_section(text, r'6\.\s*Test procedures|6 Test procedures', max_chars=50000)
        print(f"  ✅ ANSI C63.10: {len(sections['ansi_c63_10']):,}자")

    # Test Report - 시험 결과 섹션
    report_path = BASE_DIR / "AIdata/Testreport/S-4791615583-E11V1_UNII_6E.txt"
    if report_path.exists():
        with open(report_path, 'r', encoding='utf-8') as f:
            text = f.read()
        # 시험 결과 위주로 추출
        sections['report'] = text[:80000]  # 앞부분 (일반적으로 요약 + 결과)
        print(f"  ✅ Report: {len(sections['report']):,}자")

    total_chars = sum(len(s) for s in sections.values())
    print(f"\n  📊 총 텍스트: {total_chars:,}자 (약 {total_chars//3000}K 토큰)")

    return sections


def generate_cross_qa(client, sections: dict, focus: str = "all") -> list:
    """크로스 레퍼런스 Q&A 생성"""

    focus_instructions = {
        "limits": """
포커스: 제한치 vs 실측값
- 규격의 제한치 (dBm, W, MHz 등)
- 레포트의 실제 측정값
- 마진 계산
- Pass/Fail 판정 기준
""",
        "procedures": """
포커스: 시험 절차
- 규격이 요구하는 측정 조건 (RBW, Detector 등)
- KDB의 구체적 절차
- 레포트에서 실제 사용한 설정
- 측정 순서 및 방법
""",
        "equipment": """
포커스: 장비 및 셋업
- 필요한 측정 장비
- 시험 셋업 구성
- 케이블/어댑터 연결
- 교정 요구사항
""",
        "tips": """
포커스: 실무 팁
- 마진이 적은 항목
- 자주 실패하는 케이스
- 주의사항
- 권장 사항
""",
        "all": """
포커스: 종합 (제한치, 절차, 장비, 팁 모두 포함)
각 Q&A에 가능한 모든 정보를 포함하세요.
"""
    }

    prompt = f"""당신은 FCC RF 인증 시험 전문가입니다.
아래 규격들과 실제 시험 레포트를 분석하여, 규격과 실무를 연결하는 종합 Q&A를 생성하세요.

## 규격 문서들

### Part 2 (일반 규정 - RF 측정)
{sections.get('part_2', 'N/A')[:20000]}

### Part 15E (UNII 규정)
{sections.get('part_15e', 'N/A')[:25000]}

### KDB 789033 (UNII 시험 절차)
{sections.get('kdb_789033', 'N/A')[:30000]}

### KDB 987594 (6GHz 요구사항)
{sections.get('kdb_987594', 'N/A')[:40000]}

### KDB 662911 (MIMO/다중송신)
{sections.get('kdb_662911', 'N/A')[:20000]}

### ANSI C63.10-2020 (측정 표준)
{sections.get('ansi_c63_10', 'N/A')[:25000]}

## 실제 시험 레포트 (UNII 6E WLAN)
{sections.get('report', 'N/A')[:40000]}

## 생성 규칙

{focus_instructions.get(focus, focus_instructions['all'])}

1. 규격의 요구사항과 레포트의 실제 시험을 연결
2. 각 답변에 다음 포함:
   - 📋 규격 요구사항 (조항 번호)
   - 📝 시험 절차 (KDB 섹션)
   - 📘 측정 표준 (해당시)
   - 🔧 실제 시험 (레포트 데이터)
   - ⚠️ 실무 팁 (해당시)

3. 한국어로 작성
4. 구체적인 수치와 조항 번호 포함

## 출력 형식 (JSON)

```json
[
  {{
    "question": "질문",
    "answer": "종합 답변 (규격+절차+실제)",
    "category": "카테고리",
    "focus": "{focus}",
    "cross_references": {{
      "ecfr": ["§15.407(a)"],
      "kdb": ["KDB 987594 Section 5"],
      "standard": ["ANSI C63.10"],
      "report": ["Section 4.2"]
    }}
  }}
]
```

15-20개의 종합 Q&A를 생성하세요. JSON만 출력하세요.
"""

    print(f"\n🤖 Claude API 호출 중 (focus: {focus})...")
    print(f"   입력 토큰: 약 {len(prompt)//3:,}")

    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=8000,
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

        qa_pairs = json.loads(json_str.strip())
        print(f"   ✅ 생성 완료: {len(qa_pairs)}개 Q&A")

        return qa_pairs

    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return []


def main():
    print("=" * 60)
    print("크로스 레퍼런스 Q&A 생성")
    print("UNII 6E WLAN 패키지")
    print("=" * 60)

    # Claude 클라이언트
    client = get_claude_client()
    if not client:
        return

    # 핵심 섹션 로드
    sections = load_key_sections()

    if not sections:
        print("❌ 섹션 로드 실패")
        return

    # 포커스별 Q&A 생성
    all_qa = []
    focuses = ["limits", "procedures", "equipment", "tips"]

    for focus in focuses:
        print(f"\n{'─' * 40}")
        qa_pairs = generate_cross_qa(client, sections, focus)
        all_qa.extend(qa_pairs)
        time.sleep(1)  # API 호출 간격

    # 기존 Q&A 로드 및 병합
    qa_file = BASE_DIR / "aidata" / "qa_pairs.json"
    if qa_file.exists():
        with open(qa_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        existing_qa = existing_data.get('qa_pairs', [])
    else:
        existing_qa = []

    # 크로스 Q&A 표시 추가
    for qa in all_qa:
        qa['is_cross_reference'] = True
        qa['package'] = 'UNII_6E_WLAN_001'
        qa['source_type'] = 'cross_reference'

    # 병합
    final_qa = existing_qa + all_qa

    # 저장
    output_data = {
        "generated_at": datetime.now().isoformat(),
        "total_qa_pairs": len(final_qa),
        "cross_reference_count": len(all_qa),
        "qa_pairs": final_qa
    }

    with open(qa_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"✅ 완료!")
    print(f"   - 기존 Q&A: {len(existing_qa)}개")
    print(f"   - 새 크로스 Q&A: {len(all_qa)}개")
    print(f"   - 총합: {len(final_qa)}개")
    print(f"   - 저장: {qa_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
