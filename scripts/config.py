"""
AI 자동화 시스템 - 설정 파일
"""
import os
from pathlib import Path

# 기본 경로 설정
BASE_DIR = Path(r"C:\Users\younh\Documents\Ai model")
AIDATA_DIR = BASE_DIR / "aidata"
RAW_DATA_DIR = AIDATA_DIR / "raw_data"
PROCESSED_DATA_DIR = AIDATA_DIR / "processed_data"
SCRIPTS_DIR = BASE_DIR / "scripts"
LOGS_DIR = BASE_DIR / "logs"

# 데이터 소스별 경로
ECFR_DIR = RAW_DATA_DIR / "ecfr"
KDB_DIR = RAW_DATA_DIR / "kdb"
RSS_DIR = RAW_DATA_DIR / "rss"

# 소스 파일 경로
FCC_SITES_FILE = AIDATA_DIR / "fcc_sites base.txt"

# 스크래핑 설정
REQUEST_DELAY = 2  # 요청 간 대기 시간 (초)
REQUEST_TIMEOUT = 30  # 요청 타임아웃 (초)
MAX_RETRIES = 3  # 최대 재시도 횟수

# 사용자 에이전트
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# 로깅 설정
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_FILE = LOGS_DIR / "scraper.log"
