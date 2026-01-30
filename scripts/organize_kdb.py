"""
KDB 파일 정리 스크립트
- 기존 FCC 폴더의 PDF 파일을 raw_data/kdb로 복사
- 파일명에서 KDB 번호 추출
- 메타데이터 생성
"""

import os
import re
import json
import shutil
from pathlib import Path
from datetime import datetime

# 경로 설정
BASE_DIR = Path(r"C:\Users\younh\Documents\Ai model")
FCC_DIR = BASE_DIR / "aidata" / "FCC"
KDB_DIR = BASE_DIR / "aidata" / "raw_data" / "kdb"

KDB_DIR.mkdir(parents=True, exist_ok=True)

def parse_filename(filename: str) -> dict:
    """
    파일명 파싱
    예: T-23-024 (FCC IC R E) 987594 D01 U-NII 6GHz General Requirements v02r02.pdf
    - T-XX-XXX: 회사 저장번호 (무시)
    - (FCC IC R E): 카테고리 (무시)
    - 987594: KDB 번호
    - D01: 문서 번호
    - 나머지: 제목 및 버전
    """
    result = {
        'original_filename': filename,
        'kdb_number': None,
        'doc_number': None,
        'title': None,
        'version': None
    }

    # 회사 저장번호와 카테고리 제거
    # 패턴: T-XX-XXX(FCC IC R E) 또는 T-XX-XXX (FCC IC R E)
    cleaned = re.sub(r'^T-\d+-\d+\s*\(FCC IC R E\)\s*', '', filename)

    # KDB 번호 추출 (6자리 숫자)
    kdb_match = re.search(r'(\d{6})', cleaned)
    if kdb_match:
        result['kdb_number'] = kdb_match.group(1)

    # 문서 번호 추출 (D01, D02 등)
    doc_match = re.search(r'(D\d+)', cleaned)
    if doc_match:
        result['doc_number'] = doc_match.group(1)

    # 버전 추출 (v01, v02r01 등)
    version_match = re.search(r'(v\d+(?:r\d+)?)', cleaned, re.IGNORECASE)
    if version_match:
        result['version'] = version_match.group(1)

    # 제목 추출 (KDB 번호와 문서 번호 뒤, 버전 앞)
    title_match = re.search(r'D\d+\s+(.+?)\s+v\d+', cleaned, re.IGNORECASE)
    if title_match:
        result['title'] = title_match.group(1).strip()
    else:
        # 대체 방법: KDB 번호 뒤 전체
        title_match = re.search(r'\d{6}\s+D\d+\s+(.+?)\.pdf', cleaned, re.IGNORECASE)
        if title_match:
            result['title'] = title_match.group(1).strip()

    return result

def organize_files():
    """파일 정리 및 복사"""
    print("=" * 60)
    print("KDB 파일 정리 시작")
    print("=" * 60)

    # PDF 파일만 처리
    pdf_files = list(FCC_DIR.glob("*.pdf"))
    print(f"발견된 PDF 파일: {len(pdf_files)}개")

    # KDB별로 그룹화
    kdb_groups = {}

    for pdf_file in pdf_files:
        info = parse_filename(pdf_file.name)

        if not info['kdb_number']:
            print(f"  [건너뜀] KDB 번호 없음: {pdf_file.name}")
            continue

        kdb_num = info['kdb_number']
        if kdb_num not in kdb_groups:
            kdb_groups[kdb_num] = []

        kdb_groups[kdb_num].append({
            'source_path': pdf_file,
            'info': info
        })

    print(f"\n고유 KDB 번호: {len(kdb_groups)}개")

    # 파일 복사 및 메타데이터 생성
    for kdb_num, files in kdb_groups.items():
        print(f"\nKDB {kdb_num}: {len(files)}개 문서")

        # KDB별 폴더 생성
        kdb_folder = KDB_DIR / f"KDB_{kdb_num}"
        kdb_folder.mkdir(exist_ok=True)

        metadata = {
            'kdb_number': kdb_num,
            'documents': [],
            'organized_at': datetime.now().isoformat()
        }

        for file_info in files:
            src = file_info['source_path']
            info = file_info['info']

            # 새 파일명 생성
            doc_num = info['doc_number'] or 'D00'
            version = info['version'] or 'v00'
            title = info['title'] or 'document'
            # 파일명 안전하게 만들기
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)[:50]
            new_name = f"KDB_{kdb_num}_{doc_num}_{safe_title}_{version}.pdf"

            dst = kdb_folder / new_name

            # 복사
            shutil.copy2(src, dst)
            print(f"  -> {new_name}")

            metadata['documents'].append({
                'original_filename': info['original_filename'],
                'new_filename': new_name,
                'doc_number': doc_num,
                'title': title,
                'version': version
            })

        # 메타데이터 저장
        meta_path = kdb_folder / "metadata.json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"정리 완료: {len(kdb_groups)}개 KDB, {len(pdf_files)}개 문서")
    print(f"저장 위치: {KDB_DIR}")
    print("=" * 60)

    return kdb_groups

if __name__ == '__main__':
    organize_files()
