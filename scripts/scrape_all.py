"""
전체 데이터 수집 스크립트
- eCFR 17개 문서
- RSS 34개 문서
"""

import sys
sys.path.insert(0, r"C:\Users\younh\Documents\Ai model\scripts")

import time
import logging
from pathlib import Path
from scraper import ECFRScraper, RSSScraper, logger

# 경로 설정
BASE_DIR = Path(r"C:\Users\younh\Documents\Ai model")
RAW_DATA_DIR = BASE_DIR / "aidata" / "raw_data"

# eCFR 목록
ECFR_DOCS = [
    ("CFR_Part_2", "https://www.ecfr.gov/current/title-47/chapter-I/subchapter-A/part-2"),
    ("CFR_Part_15B", "https://www.ecfr.gov/current/title-47/chapter-I/subchapter-A/part-15/subpart-B"),
    ("CFR_Part_15C", "https://www.ecfr.gov/current/title-47/chapter-I/subchapter-A/part-15/subpart-C"),
    ("CFR_Part_15E", "https://www.ecfr.gov/current/title-47/chapter-I/subchapter-A/part-15/subpart-E"),
    ("CFR_Part_22H", "https://www.ecfr.gov/current/title-47/chapter-I/subchapter-B/part-22#subpart-H"),
    ("CFR_Part_24E", "https://www.ecfr.gov/current/title-47/chapter-I/subchapter-B/part-24#subpart-E"),
    ("CFR_Part_27", "https://www.ecfr.gov/current/title-47/chapter-I/subchapter-B/part-27"),
    ("CFR_Part_25", "https://www.ecfr.gov/current/title-47/chapter-I/subchapter-B/part-25"),
    ("CFR_Part_95", "https://www.ecfr.gov/current/title-47/chapter-I/subchapter-D/part-95"),
    ("CFR_Part_97", "https://www.ecfr.gov/current/title-47/chapter-I/subchapter-D/part-97"),
    ("CFR_Part_101", "https://www.ecfr.gov/current/title-47/chapter-I/subchapter-D/part-101"),
    ("CFR_Part_18", "https://www.ecfr.gov/current/title-47/chapter-I/subchapter-A/part-18"),
    ("CFR_Part_20", "https://www.ecfr.gov/current/title-47/chapter-I/subchapter-B/part-20"),
    ("CFR_Part_74", "https://www.ecfr.gov/current/title-47/chapter-I/subchapter-C/part-74"),
    ("CFR_Part_96", "https://www.ecfr.gov/current/title-47/chapter-I/subchapter-D/part-96"),
    ("CFR_Part_90", "https://www.ecfr.gov/current/title-47/chapter-I/subchapter-D/part-90"),
    ("CFR_Part_30", "https://www.ecfr.gov/current/title-47/chapter-I/subchapter-B/part-30"),
]

# RSS 목록
RSS_DOCS = [
    ("RSS-102", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-102-radio-frequency-rf-exposure-compliance-radiocommunication-apparatus-all-frequency-bands"),
    ("RSS-111", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-111-broadband-public-safety-equipment-operating-band-4940-4990-mhz"),
    ("RSS-119", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/broadcasting-equipment-standards/broadcasting-equipment-technical-standards-betsdevices-and-equipment/broadcasting-equipment-standards/broadcasting-certificate-exempt-radio-apparatus-0"),
    ("RSS-123", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/rss-123-licensed-wireless-microphones"),
    ("RSS-125", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/broadcasting-equipment-standards/broadcasting-equipment-technical-standards-betsdevices-and-equipment/broadcasting-equipment-standards/broadcasting-certificate-exempt-radio-apparatus-7"),
    ("RSS-130", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-130-equipment-operating-frequency-bands-617-652-mhz-663-698-mhz-698-756-mhz-and-777-787-mhz"),
    ("RSS-131", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/rss-131-zone-enhancers"),
    ("RSS-132", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/broadcasting-equipment-standards/broadcasting-equipment-technical-standards-betsdevices-and-equipment/broadcasting-equipment-standards/broadcasting-certificate-exempt-radio-apparatus-21"),
    ("RSS-133", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-133-2-ghz-personal-communications-services"),
    ("RSS-134", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/rss-134-900-mhz-narrowband-personal-communication-service"),
    ("RSS-137", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/rss-137-location-and-monitoring-service-band-902-928-mhz"),
    ("RSS-139", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-139-advanced-wireless-services-equipment-operating-bands-1710-1780-mhz-and-2110-2200-mhz"),
    ("RSS-140", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-140-equipment-operating-public-safety-broadband-frequency-bands-758-768-mhz-and-788-798-mhz"),
    ("RSS-142", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/rss-142-narrowband-multipoint-communication-systems-bands-14295-1432-mhz"),
    ("RSS-181", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-181-coast-and-ship-station-equipment-operating-maritime-service-frequency-range-1605-28000-khz"),
    ("RSS-191", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/broadcasting-equipment-standards/broadcasting-equipment-technical-standards-betsdevices-and-equipment/broadcasting-equipment-standards/broadcasting-certificate-exempt-radio-apparatus-19"),
    ("RSS-192", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-192-flexible-use-broadband-equipment-operating-band-3450-3900-mhz"),
    ("RSS-194", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-194-fixed-wireless-access-equipment-operating-band-953-960-mhz"),
    ("RSS-195", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/rss-195-wireless-communication-service-wcs-equipment-operating-bands-2305-2320-mhz-and-2345-2360-mhz"),
    ("RSS-197", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-197-wireless-broadband-access-equipment-operating-band-3650-3700-mhz"),
    ("RSS-198", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/flexible-use-broadband-equipment-operating-band-3900-3980-mhz"),
    ("RSS-199", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-standards-procedures-rsp/rss-199-broadband-radio-service-brs-equipment-operating-band-2500-2690-mhz"),
    ("RSS-210", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-210-licence-exempt-radio-apparatus-category-i-equipment"),
    ("RSS-213", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/rss-213-2-ghz-licence-exempt-personal-communications-services-le-pcs-devices"),
    ("RSS-216", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-216-wireless-power-transfer-devices"),
    ("RSS-220", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-220-devices-using-ultra-wideband-uwb-technology"),
    ("RSS-222", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-222-white-space-devices-wsds"),
    ("RSS-243", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-243-medical-devices-operating-401-406-mhz-frequency-band"),
    ("RSS-244", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-244-medical-devices-operating-band-413-457-mhz"),
    ("RSS-247", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-247-digital-transmission-systems-dtss-frequency-hopping-systems-fhss-and-licence-exempt-local"),
    ("RSS-248", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-248-radio-local-area-network-rlan-devices-operating-5925-7125-mhz-band"),
    ("RSS-252", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-252-intelligent-transportation-systems-dedicated-short-range-communications-dsrc-board-unit-obu"),
    ("RSS-310", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-310-licence-exempt-radio-apparatus-category-ii-equipment"),
    ("RSS-GEN", "https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-gen-general-requirements-compliance-radio-apparatus"),
]


def scrape_ecfr():
    """eCFR 전체 수집"""
    logger.info("=" * 60)
    logger.info("eCFR 수집 시작 (17개)")
    logger.info("=" * 60)

    scraper = ECFRScraper()
    success = 0
    failed = []

    for doc_id, url in ECFR_DOCS:
        logger.info(f"\n[{success+1}/{len(ECFR_DOCS)}] {doc_id}")
        try:
            result = scraper.scrape(url, doc_id)
            if result:
                success += 1
            else:
                failed.append(doc_id)
        except Exception as e:
            logger.error(f"Error: {e}")
            failed.append(doc_id)
        time.sleep(1)  # Rate limiting

    logger.info(f"\neCFR 완료: {success}/{len(ECFR_DOCS)}")
    if failed:
        logger.warning(f"실패: {failed}")
    return success


def scrape_rss():
    """RSS 전체 수집"""
    logger.info("=" * 60)
    logger.info("RSS 수집 시작 (34개)")
    logger.info("=" * 60)

    scraper = RSSScraper()
    success = 0
    failed = []

    for doc_id, url in RSS_DOCS:
        logger.info(f"\n[{success+1}/{len(RSS_DOCS)}] {doc_id}")
        try:
            result = scraper.scrape(url, doc_id)
            if result:
                success += 1
            else:
                failed.append(doc_id)
        except Exception as e:
            logger.error(f"Error: {e}")
            failed.append(doc_id)
        time.sleep(1)  # Rate limiting

    logger.info(f"\nRSS 완료: {success}/{len(RSS_DOCS)}")
    if failed:
        logger.warning(f"실패: {failed}")
    return success


def main():
    logger.info("=" * 60)
    logger.info("전체 데이터 수집 시작")
    logger.info("=" * 60)

    # eCFR 수집
    ecfr_count = scrape_ecfr()

    # RSS 수집
    rss_count = scrape_rss()

    # 요약
    logger.info("\n" + "=" * 60)
    logger.info("수집 완료 요약")
    logger.info("=" * 60)
    logger.info(f"eCFR: {ecfr_count}/{len(ECFR_DOCS)}")
    logger.info(f"RSS: {rss_count}/{len(RSS_DOCS)}")
    logger.info(f"KDB: 32개 (기존 로컬 파일)")
    logger.info("=" * 60)

    return ecfr_count, rss_count


if __name__ == '__main__':
    main()
