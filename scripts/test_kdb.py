"""KDB 스크래핑 테스트"""
import sys
sys.path.insert(0, r"C:\Users\younh\Documents\Ai model\scripts")

from scraper import KDBScraper, logger

def test_kdb():
    logger.info("KDB 스크래핑 테스트 시작")

    scraper = KDBScraper()
    result = scraper.scrape(
        url='https://apps.fcc.gov/oetcf/kdb/forms/FTSSearchResultPage.cfm?id=21124&switch=P',
        doc_id='KDB_558074'
    )

    if result:
        logger.info(f"성공: {result.file_path}")
    else:
        logger.error("실패")

    # 드라이버 정리
    scraper._close_driver()

if __name__ == '__main__':
    test_kdb()
