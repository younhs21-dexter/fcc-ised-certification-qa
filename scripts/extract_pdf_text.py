# -*- coding: utf-8 -*-
"""PDF 텍스트 추출 스크립트"""

import sys
import io
import fitz  # PyMuPDF
from pathlib import Path

# Windows 콘솔 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent.parent


def extract_pdf_to_text(pdf_path: Path, output_path: Path = None) -> str:
    """PDF에서 텍스트 추출"""
    try:
        doc = fitz.open(pdf_path)
        text_content = []

        for page_num, page in enumerate(doc, 1):
            text = page.get_text()
            if text.strip():
                text_content.append(f"--- Page {page_num} ---\n{text}")

        doc.close()

        full_text = "\n\n".join(text_content)

        # 출력 파일 저장
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_text)

        return full_text

    except Exception as e:
        print(f"  ❌ 오류: {e}")
        return ""


def main():
    print("=" * 60)
    print("PDF 텍스트 추출 - UNII 6E WLAN 패키지")
    print("=" * 60)

    # 추출할 파일 목록
    files_to_extract = [
        # KDB 789033
        {
            "pdf": BASE_DIR / "AIdata/raw_data/kdb/KDB_789033/KDB_789033_D02_General UNII Test Procedures New Rules_v02r01.pdf",
            "txt": BASE_DIR / "AIdata/raw_data/kdb/KDB_789033/KDB_789033_D02.txt"
        },
        # KDB 987594
        {
            "pdf": BASE_DIR / "AIdata/raw_data/kdb/KDB_987594/KDB_987594_D01_U-NII 6GHz General Requirements_v03.pdf",
            "txt": BASE_DIR / "AIdata/raw_data/kdb/KDB_987594/KDB_987594_D01.txt"
        },
        {
            "pdf": BASE_DIR / "AIdata/raw_data/kdb/KDB_987594/KDB_987594_D02_U-NII 6 GHz EMC Measurement_v03.pdf",
            "txt": BASE_DIR / "AIdata/raw_data/kdb/KDB_987594/KDB_987594_D02.txt"
        },
        {
            "pdf": BASE_DIR / "AIdata/raw_data/kdb/KDB_987594/KDB_987594_D03_U-NII 6 GHz QA_v03.pdf",
            "txt": BASE_DIR / "AIdata/raw_data/kdb/KDB_987594/KDB_987594_D03.txt"
        },
        {
            "pdf": BASE_DIR / "AIdata/raw_data/kdb/KDB_987594/KDB_987594_D04_UN6GHZ Pre-Approval Guidance Checklist_v03.pdf",
            "txt": BASE_DIR / "AIdata/raw_data/kdb/KDB_987594/KDB_987594_D04.txt"
        },
        # KDB 662911
        {
            "pdf": BASE_DIR / "AIdata/raw_data/kdb/KDB_662911/KDB_662911_D01_Multiple Transmitter Output_v02r01.pdf",
            "txt": BASE_DIR / "AIdata/raw_data/kdb/KDB_662911/KDB_662911_D01.txt"
        },
        {
            "pdf": BASE_DIR / "AIdata/raw_data/kdb/KDB_662911/KDB_662911_D02_MIMO with Cross Polarized Antenna_v01.pdf",
            "txt": BASE_DIR / "AIdata/raw_data/kdb/KDB_662911/KDB_662911_D02.txt"
        },
        {
            "pdf": BASE_DIR / "AIdata/raw_data/kdb/KDB_662911/KDB_662911_D03_MIMO Antenna Gain Measurement_v01.pdf",
            "txt": BASE_DIR / "AIdata/raw_data/kdb/KDB_662911/KDB_662911_D03.txt"
        },
        # ANSI C63.10
        {
            "pdf": BASE_DIR / "AIdata/global/ANSI c63.10 2020.pdf",
            "txt": BASE_DIR / "AIdata/global/ANSI_C63.10_2020.txt"
        },
        # Test Report
        {
            "pdf": BASE_DIR / "AIdata/Testreport/S-4791615583-E11V1 FCC Report UNII(6E) WLAN.pdf",
            "txt": BASE_DIR / "AIdata/Testreport/S-4791615583-E11V1_UNII_6E.txt"
        },
    ]

    success_count = 0
    fail_count = 0

    for item in files_to_extract:
        pdf_path = item["pdf"]
        txt_path = item["txt"]

        print(f"\n📄 {pdf_path.name}")

        if not pdf_path.exists():
            print(f"  ❌ 파일 없음: {pdf_path}")
            fail_count += 1
            continue

        text = extract_pdf_to_text(pdf_path, txt_path)

        if text:
            # 페이지 수와 글자 수 계산
            pages = text.count("--- Page ")
            chars = len(text)
            print(f"  ✅ 추출 완료: {pages}페이지, {chars:,}자")
            print(f"  → {txt_path.name}")
            success_count += 1
        else:
            fail_count += 1

    print("\n" + "=" * 60)
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {fail_count}개")
    print("=" * 60)


if __name__ == "__main__":
    main()
