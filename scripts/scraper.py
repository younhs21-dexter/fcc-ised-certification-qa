"""
AI 자동화 시스템 - 데이터 수집 스크립트
FCC/ISED 규격 문서 수집용
"""

import os
import re
import time
import json
import logging
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict

# 설정 임포트
try:
    from config import *
except ImportError:
    # 직접 실행 시 경로 설정
    BASE_DIR = Path(r"C:\Users\younh\Documents\Ai model")
    AIDATA_DIR = BASE_DIR / "aidata"
    RAW_DATA_DIR = AIDATA_DIR / "raw_data"
    ECFR_DIR = RAW_DATA_DIR / "ecfr"
    KDB_DIR = RAW_DATA_DIR / "kdb"
    RSS_DIR = RAW_DATA_DIR / "rss"
    LOGS_DIR = BASE_DIR / "logs"
    REQUEST_DELAY = 2
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    LOG_FILE = LOGS_DIR / "scraper.log"

# 디렉토리 생성
for dir_path in [ECFR_DIR, KDB_DIR, RSS_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ScrapedDocument:
    """수집된 문서 메타데이터"""
    source_type: str  # ecfr, kdb, rss
    doc_id: str
    title: str
    url: str
    content_type: str  # html, pdf
    file_path: str
    scraped_at: str
    metadata: Dict


class BaseScraper:
    """스크래퍼 기본 클래스"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })

    def fetch(self, url: str, retries: int = MAX_RETRIES) -> Optional[requests.Response]:
        """URL 가져오기 (재시도 로직 포함)"""
        for attempt in range(retries):
            try:
                logger.info(f"Fetching: {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                time.sleep(REQUEST_DELAY)
                return response
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(REQUEST_DELAY * (attempt + 1))
        logger.error(f"Failed to fetch: {url}")
        return None

    def save_content(self, content: str | bytes, file_path: Path, binary: bool = False):
        """콘텐츠 저장"""
        mode = 'wb' if binary else 'w'
        encoding = None if binary else 'utf-8'
        with open(file_path, mode, encoding=encoding) as f:
            f.write(content)
        logger.info(f"Saved: {file_path}")


class ECFRScraper(BaseScraper):
    """eCFR (전자 연방 규정집) 스크래퍼 - API 버전"""

    def __init__(self):
        super().__init__()
        # eCFR Renderer API 엔드포인트
        self.api_base = "https://www.ecfr.gov/api/renderer/v1/content/enhanced/current"

    def scrape(self, url: str, doc_id: str) -> Optional[ScrapedDocument]:
        """eCFR 규정 수집 (API 사용)"""
        logger.info(f"Scraping eCFR: {doc_id}")

        # URL에서 경로 추출 (예: title-47/chapter-I/subchapter-A/part-15/subpart-B)
        match = re.search(r'/current/(.+)$', url)
        if not match:
            logger.error(f"Invalid eCFR URL format: {url}")
            return None

        path = match.group(1)

        # API URL 구성
        api_url = self._build_api_url(path)
        logger.info(f"Using API: {api_url}")

        response = self.fetch(api_url)
        if not response:
            logger.error(f"API fetch failed for {doc_id}")
            return None

        # JSON 응답 파싱
        try:
            data = response.json()
        except json.JSONDecodeError:
            # HTML로 반환된 경우
            data = {'content': response.text}

        # HTML 콘텐츠 추출
        if isinstance(data, dict) and 'content' in data:
            html_content = data.get('content', '')
        else:
            html_content = response.text

        # HTML 파싱 및 텍스트 추출
        soup = BeautifulSoup(html_content, 'html.parser')
        content_text = self._extract_structured_text(soup)

        # 저장
        file_path = ECFR_DIR / f"{doc_id}.txt"
        self.save_content(content_text, file_path)

        # HTML 원본도 저장
        html_path = ECFR_DIR / f"{doc_id}.html"
        self.save_content(html_content, html_path)

        # JSON 메타데이터 저장
        metadata = {
            'url': url,
            'api_url': api_url,
            'path': path,
            'scraped_at': datetime.now().isoformat()
        }
        meta_path = ECFR_DIR / f"{doc_id}_meta.json"
        self.save_content(json.dumps(metadata, indent=2), meta_path)

        return ScrapedDocument(
            source_type='ecfr',
            doc_id=doc_id,
            title=doc_id,
            url=url,
            content_type='html',
            file_path=str(file_path),
            scraped_at=datetime.now().isoformat(),
            metadata=metadata
        )

    def _build_api_url(self, path: str) -> str:
        """웹 URL 경로를 API URL로 변환"""
        # 예: title-47/chapter-I/subchapter-A/part-15/subpart-B
        # -> /title-47?chapter=I&subchapter=A&part=15&subpart=B
        parts = path.split('/')
        if not parts:
            return f"{self.api_base}/title-47"

        title_part = parts[0]  # title-47
        params = []

        for part in parts[1:]:
            if '-' in part:
                key, value = part.split('-', 1)
                # chapter-I -> chapter=I
                params.append(f"{key}={value}")

        if params:
            return f"{self.api_base}/{title_part}?{'&'.join(params)}"
        else:
            return f"{self.api_base}/{title_part}"

    def _extract_structured_text(self, soup) -> str:
        """구조화된 텍스트 추출"""
        # 불필요한 요소 제거
        for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()

        lines = []

        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div']):
            if element.name.startswith('h'):
                level = int(element.name[1])
                prefix = '#' * level
                text = element.get_text(strip=True)
                if text:
                    lines.append(f"\n{prefix} {text}\n")
            elif element.name == 'p':
                text = element.get_text(strip=True)
                if text and len(text) > 10:  # 짧은 텍스트 무시
                    lines.append(text + '\n')
            elif element.name == 'div' and element.get('class'):
                # 특정 클래스만 처리
                classes = element.get('class', [])
                if any(c in classes for c in ['section', 'paragraph', 'content']):
                    text = element.get_text(strip=True)
                    if text and len(text) > 20:
                        lines.append(text + '\n')

        result = '\n'.join(lines)
        result = re.sub(r'\n{3,}', '\n\n', result)
        return result

    def _extract_text(self, element) -> str:
        """HTML 요소에서 텍스트 추출"""
        # 스크립트, 스타일 제거
        for tag in element.find_all(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()

        text = element.get_text(separator='\n', strip=True)
        # 연속 공백 정리
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text


class KDBScraper(BaseScraper):
    """FCC KDB (Knowledge Database) 스크래퍼 - Selenium 지원"""

    BASE_URL = "https://apps.fcc.gov"

    def __init__(self):
        super().__init__()
        self.driver = None

    def _init_driver(self):
        """Selenium WebDriver 초기화 (Edge 우선)"""
        if self.driver is not None:
            return

        # Edge 먼저 시도 (Windows에 기본 설치됨)
        try:
            from selenium import webdriver
            from selenium.webdriver.edge.service import Service as EdgeService
            from selenium.webdriver.edge.options import Options as EdgeOptions
            from webdriver_manager.microsoft import EdgeChromiumDriverManager

            edge_options = EdgeOptions()
            edge_options.add_argument('--headless')
            edge_options.add_argument('--no-sandbox')
            edge_options.add_argument('--disable-dev-shm-usage')
            edge_options.add_argument(f'user-agent={USER_AGENT}')

            service = EdgeService(EdgeChromiumDriverManager().install())
            self.driver = webdriver.Edge(service=service, options=edge_options)
            logger.info("Edge WebDriver initialized")
            return
        except Exception as e:
            logger.warning(f"Edge WebDriver failed: {e}")

        # Chrome 시도
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service as ChromeService
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            from webdriver_manager.chrome import ChromeDriverManager

            chrome_options = ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument(f'user-agent={USER_AGENT}')

            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Chrome WebDriver initialized")
        except Exception as e:
            logger.error(f"Failed to initialize any WebDriver: {e}")
            self.driver = None

    def _close_driver(self):
        """WebDriver 종료"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def scrape(self, url: str, doc_id: str) -> Optional[ScrapedDocument]:
        """KDB 문서 수집 (Selenium 사용)"""
        logger.info(f"Scraping KDB: {doc_id}")

        # 먼저 일반 요청 시도
        response = self.fetch(url)
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
        else:
            # Selenium으로 대체
            logger.info("Trying Selenium for KDB...")
            self._init_driver()
            if not self.driver:
                logger.error("WebDriver not available")
                return None

            try:
                self.driver.get(url)
                time.sleep(3)  # 페이지 로딩 대기
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
            except Exception as e:
                logger.error(f"Selenium error: {e}")
                return None

        # 문서 정보 추출
        title = self._extract_title(soup)
        pdf_links = self._find_pdf_links(soup)

        if not pdf_links:
            logger.warning(f"No PDF links found for {doc_id}")
            # HTML 콘텐츠라도 저장
            file_path = KDB_DIR / f"{doc_id}.html"
            self.save_content(response.text, file_path)
            return ScrapedDocument(
                source_type='kdb',
                doc_id=doc_id,
                title=title,
                url=url,
                content_type='html',
                file_path=str(file_path),
                scraped_at=datetime.now().isoformat(),
                metadata={'note': 'No PDF found, saved HTML'}
            )

        # PDF 다운로드
        downloaded_files = []
        for i, pdf_info in enumerate(pdf_links):
            pdf_url = pdf_info['url']
            pdf_name = pdf_info['name']

            # 파일명 정리
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', pdf_name)
            file_path = KDB_DIR / f"{doc_id}_{i+1}_{safe_name}.pdf"

            pdf_response = self.fetch(pdf_url)
            if pdf_response:
                self.save_content(pdf_response.content, file_path, binary=True)
                downloaded_files.append(str(file_path))

        # 메타데이터 저장
        metadata = {
            'title': title,
            'url': url,
            'pdf_links': pdf_links,
            'downloaded_files': downloaded_files,
            'scraped_at': datetime.now().isoformat()
        }
        meta_path = KDB_DIR / f"{doc_id}_meta.json"
        self.save_content(json.dumps(metadata, indent=2, ensure_ascii=False), meta_path)

        return ScrapedDocument(
            source_type='kdb',
            doc_id=doc_id,
            title=title,
            url=url,
            content_type='pdf',
            file_path=downloaded_files[0] if downloaded_files else '',
            scraped_at=datetime.now().isoformat(),
            metadata=metadata
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """페이지에서 문서 제목 추출"""
        # Publication Number 찾기
        pub_label = soup.find(string=re.compile(r'Publication Number', re.I))
        if pub_label:
            parent = pub_label.find_parent('tr') or pub_label.find_parent('div')
            if parent:
                return parent.get_text(strip=True)

        title_tag = soup.find('title')
        return title_tag.get_text(strip=True) if title_tag else "Unknown"

    def _find_pdf_links(self, soup: BeautifulSoup) -> List[Dict]:
        """PDF 다운로드 링크 찾기"""
        pdf_links = []

        # GetAttachment.html 패턴 찾기
        for link in soup.find_all('a', href=re.compile(r'GetAttachment\.html')):
            href = link.get('href', '')
            full_url = urljoin(self.BASE_URL, href)
            name = link.get_text(strip=True) or 'document'
            pdf_links.append({
                'url': full_url,
                'name': name
            })

        # .pdf 직접 링크도 찾기
        for link in soup.find_all('a', href=re.compile(r'\.pdf$', re.I)):
            href = link.get('href', '')
            full_url = urljoin(self.BASE_URL, href)
            name = link.get_text(strip=True) or Path(href).stem
            pdf_links.append({
                'url': full_url,
                'name': name
            })

        return pdf_links


class RSSScraper(BaseScraper):
    """ISED Canada RSS (Radio Standards Specifications) 스크래퍼"""

    def scrape(self, url: str, doc_id: str) -> Optional[ScrapedDocument]:
        """RSS 규격 수집"""
        logger.info(f"Scraping RSS: {doc_id}")

        response = self.fetch(url)
        if not response:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # 제목 추출
        title = self._extract_title(soup)

        # 본문 콘텐츠 추출
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='field--body')

        if not main_content:
            # 전체 body 사용
            main_content = soup.find('body')

        # 텍스트 추출
        content_text = self._extract_structured_text(main_content)

        # 저장
        file_path = RSS_DIR / f"{doc_id}.txt"
        self.save_content(content_text, file_path)

        # HTML도 저장 (참조용)
        html_path = RSS_DIR / f"{doc_id}.html"
        self.save_content(response.text, html_path)

        # 메타데이터 저장
        metadata = {
            'title': title,
            'url': url,
            'text_file': str(file_path),
            'html_file': str(html_path),
            'scraped_at': datetime.now().isoformat()
        }
        meta_path = RSS_DIR / f"{doc_id}_meta.json"
        self.save_content(json.dumps(metadata, indent=2, ensure_ascii=False), meta_path)

        return ScrapedDocument(
            source_type='rss',
            doc_id=doc_id,
            title=title,
            url=url,
            content_type='html',
            file_path=str(file_path),
            scraped_at=datetime.now().isoformat(),
            metadata=metadata
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """페이지 제목 추출"""
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        title = soup.find('title')
        return title.get_text(strip=True) if title else "Unknown"

    def _extract_structured_text(self, element) -> str:
        """구조화된 텍스트 추출 (헤딩 유지)"""
        if not element:
            return ""

        # 불필요한 요소 제거
        for tag in element.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()

        lines = []

        for child in element.descendants:
            if child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(child.name[1])
                prefix = '#' * level
                lines.append(f"\n{prefix} {child.get_text(strip=True)}\n")
            elif child.name == 'p':
                text = child.get_text(strip=True)
                if text:
                    lines.append(text + '\n')
            elif child.name == 'li':
                text = child.get_text(strip=True)
                if text:
                    lines.append(f"  - {text}")
            elif child.name == 'table':
                lines.append(self._extract_table(child))

        # 중복 제거 및 정리
        result = '\n'.join(lines)
        result = re.sub(r'\n{3,}', '\n\n', result)
        return result

    def _extract_table(self, table) -> str:
        """테이블을 텍스트로 변환"""
        rows = []
        for tr in table.find_all('tr'):
            cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
            rows.append(' | '.join(cells))
        return '\n'.join(rows) + '\n'


def parse_sites_file(file_path: Path) -> List[Dict]:
    """사이트 목록 파일 파싱"""
    sites = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # 형식: "번호→이름, URL" 또는 "이름, URL"
            match = re.match(r'^\s*\d+\s*[→\->]?\s*(.+?),\s*(https?://.+)$', line)
            if match:
                name = match.group(1).strip()
                url = match.group(2).strip()

                # 소스 타입 결정
                if 'ecfr.gov' in url:
                    source_type = 'ecfr'
                elif 'fcc.gov' in url and 'kdb' in url.lower():
                    source_type = 'kdb'
                elif 'ised-isde.canada.ca' in url or 'rss' in name.lower():
                    source_type = 'rss'
                else:
                    source_type = 'unknown'

                # doc_id 생성
                doc_id = re.sub(r'[^a-zA-Z0-9_-]', '_', name)

                sites.append({
                    'name': name,
                    'url': url,
                    'source_type': source_type,
                    'doc_id': doc_id
                })

    return sites


def run_test():
    """테스트 실행 - 각 타입별 1개씩"""
    logger.info("=" * 60)
    logger.info("테스트 스크래핑 시작")
    logger.info("=" * 60)

    # 테스트 대상
    test_targets = [
        {
            'name': 'CFR Part 15B',
            'url': 'https://www.ecfr.gov/current/title-47/chapter-I/subchapter-A/part-15/subpart-B',
            'source_type': 'ecfr',
            'doc_id': 'CFR_Part_15B'
        },
        {
            'name': 'KDB 558074',
            'url': 'https://apps.fcc.gov/oetcf/kdb/forms/FTSSearchResultPage.cfm?id=21124&switch=P',
            'source_type': 'kdb',
            'doc_id': 'KDB_558074'
        },
        {
            'name': 'RSS-247',
            'url': 'https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-247-digital-transmission-systems-dtss-frequency-hopping-systems-fhss-and-licence-exempt-local',
            'source_type': 'rss',
            'doc_id': 'RSS-247'
        }
    ]

    scrapers = {
        'ecfr': ECFRScraper(),
        'kdb': KDBScraper(),
        'rss': RSSScraper()
    }

    results = []

    for target in test_targets:
        logger.info(f"\n--- {target['name']} 수집 시작 ---")
        scraper = scrapers.get(target['source_type'])

        if scraper:
            try:
                result = scraper.scrape(target['url'], target['doc_id'])
                if result:
                    results.append(asdict(result))
                    logger.info(f"성공: {target['name']}")
                else:
                    logger.error(f"실패: {target['name']}")
            except Exception as e:
                logger.error(f"에러: {target['name']} - {e}")
        else:
            logger.warning(f"스크래퍼 없음: {target['source_type']}")

    # 결과 저장
    results_file = BASE_DIR / "test_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"\n결과 저장: {results_file}")
    logger.info(f"총 {len(results)}/{len(test_targets)} 문서 수집 완료")

    return results


if __name__ == '__main__':
    run_test()
