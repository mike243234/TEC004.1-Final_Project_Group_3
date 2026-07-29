import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import datetime
from concurrent.futures import ThreadPoolExecutor

from scrapers import build_scrapers
from processing import build_jobs
from database import JobDatabase
import export
import analysis
import visualization
import recommender
import reporting
DATA_DIR = os.path.join(BASE, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw_html")
DB_PATH = os.path.join(DATA_DIR, "jobs.db")
CHARTS_DIR = os.path.join(DATA_DIR, "charts")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")
MAX_PAGES = 5


def run_scraper(scraper):
    try:
        return scraper.scrape()
    except Exception:
        return []


def collect_raw_jobs():
    scrapers = build_scrapers(raw_dir=RAW_DIR, max_pages=MAX_PAGES)
    raw_jobs = []
    with ThreadPoolExecutor(max_workers=len(scrapers)) as pool:
        for result in pool.map(run_scraper, scrapers):
            raw_jobs.extend(result)
    return raw_jobs


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)

    raw_jobs = collect_raw_jobs()
    jobs = build_jobs(raw_jobs)
    print("Da thu thap {} tin tuyen dung".format(len(jobs)))
    if not jobs:
        print("Khong doc duoc tin nao. Kiem tra ket noi mang hoac chay fetch.py de luu HTML.")
        return

    export.export_json(jobs, os.path.join(DATA_DIR, "jobs.json"))
    export.export_csv(jobs, os.path.join(DATA_DIR, "jobs.csv"))

    database = JobDatabase(DB_PATH)
    database.reset()
    database.save_all(jobs)
    print("Top ky nang (truy van SQL):")
    for name, demand in database.top_skills(10):
        print("  {} - {}".format(name, demand))
    database.close()

    jobs_df, skills_df = analysis.load_jobs(DB_PATH)
    top_skills_df = analysis.top_skills(skills_df, 20)
    salary_role_df = analysis.salary_by_role(jobs_df)
    location_df = analysis.location_distribution(jobs_df)
    experience_df = analysis.experience_distribution(jobs_df)
    skill_value_df = analysis.skill_value(skills_df, 15)

    charts = {
        "skill_demand": visualization.plot_skill_demand(top_skills_df, CHARTS_DIR),
        "location": visualization.plot_location(location_df, CHARTS_DIR),
    }
    if bool((jobs_df["salary_mid"] > 0).any()):
        charts["salary_box"] = visualization.plot_salary_box(jobs_df, CHARTS_DIR)
    if bool(jobs_df["posted_date"].astype(str).str.len().gt(0).any()):
        charts["posting_trend"] = visualization.plot_posting_trend(jobs_df, CHARTS_DIR)

    recommendations = recommender.recommend_skills(skill_value_df, 10)
    gap = recommender.skill_gap(skill_value_df, ["HTML", "CSS", "JavaScript"], 8)

    reporting.generate_report(
        jobs_df, top_skills_df, salary_role_df, location_df, experience_df,
        recommendations, gap, charts, os.path.join(REPORTS_DIR, "market_report.md"),
    )
    reference_date = datetime.date(2026, 6, 19)
    reporting.generate_weekly_report(jobs_df, reference_date, os.path.join(REPORTS_DIR, "weekly_report.md"))

    print("Hoan tat. Chay 'uvicorn job_market_system.api:app --reload' de dung web app tai http://127.0.0.1:8000")


if __name__ == "__main__":
    main()
