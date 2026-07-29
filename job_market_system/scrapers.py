import os
import json
import time
import requests
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
}


def text_or(node, default=""):
    return node.get_text(" ", strip=True) if node else default


def attr_or(node, attr, default=""):
    if node is None:
        return default
    value = node.get(attr)
    if value:
        return value.strip()
    return node.get_text(" ", strip=True) or default


class BaseJobScraper(ABC):
    site_name = "base"
    prefix = "base"
    max_pages = 3
    delay = 1.0

    def __init__(self, raw_dir=None, max_pages=None):
        self.raw_dir = raw_dir
        if max_pages is not None:
            self.max_pages = max_pages
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    @abstractmethod
    def list_url(self, page):
        pass

    @abstractmethod
    def parse(self, html):
        pass

    def fetch_live(self, page):
        url = self.list_url(page)
        response = self.session.get(url, timeout=20)
        response.encoding = "utf-8"
        if response.status_code != 200:
            return ""
        return response.text

    def fetch_saved(self, page):
        if not self.raw_dir:
            return ""
        path = os.path.join(self.raw_dir, "{}_page_{}.html".format(self.prefix, page))
        if not os.path.exists(path):
            return ""
        with open(path, encoding="utf-8") as handle:
            return handle.read()

    def safe_parse(self, html):
        if not html:
            return []
        try:
            return self.parse(html)
        except Exception:
            return []

    def scrape_page(self, page):
        html = ""
        try:
            html = self.fetch_live(page)
        except Exception:
            html = ""
        jobs = self.safe_parse(html)
        if not jobs:
            jobs = self.safe_parse(self.fetch_saved(page))
        return jobs

    def scrape(self):
        results = []
        for page in range(1, self.max_pages + 1):
            jobs = self.scrape_page(page)
            for job in jobs:
                job["source"] = self.site_name
                results.append(job)
            if self.delay:
                time.sleep(self.delay)
        return results


class ITviecScraper(BaseJobScraper):
    site_name = "ITviec"
    prefix = "itviec"

    def list_url(self, page):
        return "https://itviec.com/it-jobs?page={}".format(page)

    def clean_location(self, text):
        for word in ["At office", "Hybrid", "Remote"]:
            text = text.replace(word, "")
        return text.strip() or "Hồ Chí Minh"

    def read_company(self, card):
        for link in card.select("a[href*='/companies/']"):
            name = link.get_text(strip=True)
            if name:
                return name
        return "Unknown"

    def parse(self, html):
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        for card in soup.select("div.job-card"):
            title = card.select_one("h3")
            if title is None:
                continue
            salary = card.select_one(".salary")
            location = card.select_one("div.igap-2.small-text")
            tags = [tag.get_text(strip=True) for tag in card.select("a.itag") if tag.get_text(strip=True)]
            jobs.append({
                "title": title.get_text(strip=True),
                "company": self.read_company(card),
                "salary_text": text_or(salary, "Sign in to view salary"),
                "location": self.clean_location(text_or(location)),
                "exp_text": "",
                "posted_date": "",
                "skills": tags,
            })
        return jobs


class VietnamWorksScraper(BaseJobScraper):
    site_name = "VietnamWorks"
    prefix = "vietnamworks"

    def list_url(self, page):
        return "https://www.vietnamworks.com/viec-lam?q=it&page={}".format(page)

    def parse(self, html):
        soup = BeautifulSoup(html, "html.parser")
        tag = soup.find("script", id="__NEXT_DATA__")
        if tag is None or not tag.string:
            return []
        data = json.loads(tag.string)
        page_props = data.get("props", {}).get("pageProps", {})
        items = page_props.get("outstandingJobs") or page_props.get("jobs") or []
        jobs = []
        for item in items:
            raw_date = item.get("priorityOrder", "")
            posted = raw_date.split("T")[0] if isinstance(raw_date, str) and "T" in raw_date else ""
            jobs.append({
                "title": item.get("jobTitle", ""),
                "company": item.get("company", "Unknown"),
                "salary_text": item.get("prettySalary") or item.get("salary") or "Thỏa thuận",
                "location": item.get("location", "Hồ Chí Minh"),
                "exp_text": "",
                "posted_date": posted,
                "skills": [],
            })
        return jobs


class CareerVietScraper(BaseJobScraper):
    site_name = "CareerViet"
    prefix = "careerviet"

    def list_url(self, page):
        return "https://careerviet.vn/viec-lam/cong-nghe-thong-tin-c1-trang-{}-vi.html".format(page)

    def read_location(self, card):
        location = card.select_one("div.location")
        if location is None:
            return "Hà Nội"
        parts = [li.get_text(" ", strip=True) for li in location.select("li") if li.get_text(strip=True)]
        if parts:
            return ", ".join(parts)
        return location.get_text(" ", strip=True) or "Hà Nội"

    def read_salary(self, card):
        salary = card.select_one("div.salary")
        text = text_or(salary)
        for prefix in ["Lương :", "Lương:", "Lương"]:
            if text.startswith(prefix):
                text = text[len(prefix):].strip(" :")
                break
        return text or "Thỏa thuận"

    def parse(self, html):
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        for card in soup.select("div.job-item"):
            classes = " ".join(card.get("class", []))
            if "Loading" in classes:
                continue
            link = card.select_one("h2 a.job_link") or card.select_one("a.job_link")
            if link is None:
                continue
            title = attr_or(link, "title")
            if not title:
                continue
            company = attr_or(card.select_one("a.company-name"), "title", "Unknown")
            jobs.append({
                "title": title,
                "company": company,
                "salary_text": self.read_salary(card),
                "location": self.read_location(card),
                "exp_text": "",
                "posted_date": "",
                "skills": [],
            })
        return jobs


class CareerLinkScraper(BaseJobScraper):
    site_name = "CareerLink"
    prefix = "careerlink"

    def list_url(self, page):
        return "https://www.careerlink.vn/vieclam/tim-kiem-viec-lam?keyword=it&page={}".format(page)

    def parse(self, html):
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        for card in soup.select("li.job-item.tlp-job"):
            link = card.select_one("a.job-link")
            if link is None:
                continue
            title = attr_or(link, "title")
            if not title:
                continue
            company = attr_or(card.select_one("a.job-company"), "title", "Unknown")
            salary = text_or(card.select_one("span.job-salary"), "Thỏa thuận")
            location = text_or(card.select_one("div.job-location"), "Hồ Chí Minh")
            position = text_or(card.select_one("a.job-position"))
            jobs.append({
                "title": title,
                "company": company,
                "salary_text": salary or "Thỏa thuận",
                "location": location or "Hồ Chí Minh",
                "exp_text": position,
                "posted_date": "",
                "skills": [],
            })
        return jobs


SCRAPER_CLASSES = [
    ITviecScraper,
    VietnamWorksScraper,
    CareerVietScraper,
    CareerLinkScraper,
]


def build_scrapers(raw_dir=None, max_pages=3):
    return [scraper_class(raw_dir=raw_dir, max_pages=max_pages) for scraper_class in SCRAPER_CLASSES]
