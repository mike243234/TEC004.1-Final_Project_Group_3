import os
import time
import requests
from scrapers import SCRAPER_CLASSES, HEADERS

BASE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE, "data", "raw_html")
MAX_PAGES = 5


def fetch():
    os.makedirs(RAW_DIR, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)
    for scraper_class in SCRAPER_CLASSES:
        scraper = scraper_class(raw_dir=RAW_DIR, max_pages=MAX_PAGES)
        for page in range(1, MAX_PAGES + 1):
            url = scraper.list_url(page)
            try:
                response = session.get(url, timeout=25)
                response.encoding = "utf-8"
                path = os.path.join(RAW_DIR, "{}_page_{}.html".format(scraper.prefix, page))
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(response.text)
                print("OK  {} page {} -> status {} ({} bytes)".format(scraper.prefix, page, response.status_code, len(response.text)))
            except Exception as error:
                print("ERR {} page {} -> {}".format(scraper.prefix, page, error))
            time.sleep(2)
    print("Da luu HTML vao thu muc data/raw_html")


if __name__ == "__main__":
    fetch()
