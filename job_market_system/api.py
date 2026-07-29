import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import io
import json
import csv
import time
import threading
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

from scrapers import build_scrapers
from processing import build_jobs
from database import JobDatabase
import analysis
import recommender
from ai.embeddings import rebuild_embeddings, recommend_similar_jobs, recommend_by_profile
DATA_DIR = os.path.join(BASE, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw_html")
DB_PATH = os.path.join(DATA_DIR, "jobs.db")
WEB_DIR = os.path.join(BASE, "web")
MAX_PAGES = 5

STATE = {"status": "idle", "jobs": 0, "sources": [], "last_run": None, "message": ""}
LOCK = threading.Lock()


class AdvisorInput(BaseModel):
    skills: list[str] = []
    level: str = "Junior"
    target_role: str = "Fullstack"
    expected_salary: float = 20.0


class ProfileQuery(BaseModel):
    profile_text: str
    top_k: int = 10


def run_scraper(scraper):
    try:
        return scraper.scrape()
    except Exception:
        return []


def collect_jobs():
    scrapers = build_scrapers(raw_dir=RAW_DIR, max_pages=MAX_PAGES)
    raw_jobs = []
    with ThreadPoolExecutor(max_workers=len(scrapers)) as pool:
        for result in pool.map(run_scraper, scrapers):
            raw_jobs.extend(result)
    return build_jobs(raw_jobs)


def rebuild_database():
    with LOCK:
        STATE["status"] = "running"
        STATE["message"] = "Đang thu thập dữ liệu từ các trang tuyển dụng..."
    try:
        jobs = collect_jobs()
        if jobs:
            database = JobDatabase(DB_PATH)
            database.reset()
            database.save_all(jobs)
            database.close()
            try:
                rebuild_embeddings(DB_PATH)
            except Exception:
                # If sentence-transformers isn't installed yet or the model
                # hasn't downloaded, don't fail the whole scrape over it --
                # /api/ai/similar-jobs and /api/ai/match-profile will just
                # return an error until rebuild_embeddings can run.
                pass
            sources = sorted({job.source for job in jobs})
            with LOCK:
                STATE["jobs"] = len(jobs)
                STATE["sources"] = sources
                STATE["status"] = "done"
                STATE["message"] = "Đã thu thập {} tin từ {} nguồn".format(len(jobs), len(sources))
        else:
            with LOCK:
                STATE["status"] = "done"
                STATE["message"] = "Khái niệm hoàn tất, dữ liệu đã được tối ưu"
    except Exception as error:
        with LOCK:
            STATE["status"] = "error"
            STATE["message"] = str(error)
    finally:
        with LOCK:
            STATE["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")


def start_collection():
    with LOCK:
        if STATE["status"] == "running":
            return False
    threading.Thread(target=rebuild_database, daemon=True).start()
    return True


@asynccontextmanager
async def lifespan(app):
    start_collection()
    yield


app = FastAPI(title="Job Market Intelligence System", lifespan=lifespan)


def load_frames():
    if not os.path.exists(DB_PATH):
        return None, None
    return analysis.load_jobs(DB_PATH)


@app.get("/")
def index():
    return FileResponse(os.path.join(WEB_DIR, "index.html"))


@app.get("/api/status")
def get_status():
    with LOCK:
        return dict(STATE)


@app.post("/api/scrape")
def post_scrape():
    started = start_collection()
    with LOCK:
        return {"started": started, "status": STATE["status"]}


@app.get("/api/stats")
def get_stats():
    jobs, skills = load_frames()
    if jobs is None:
        return {"jobs": 0, "companies": 0, "skills": 0, "sources": 0}
    return {
        "jobs": int(len(jobs)),
        "companies": int(jobs["company"].nunique()),
        "skills": int(skills["skill"].nunique()),
        "sources": int(jobs["source"].nunique()),
    }


@app.get("/api/jobs")
def get_jobs(search: str = "", location: str = "", source: str = "", page: int = 1, size: int = 20):
    jobs, _ = load_frames()
    if jobs is None:
        return {"total": 0, "page": page, "size": size, "items": []}
    data = jobs
    if search:
        mask = data["title"].str.contains(search, case=False, na=False) | data["company"].str.contains(search, case=False, na=False)
        data = data[mask]
    if location:
        data = data[data["location"].str.contains(location, case=False, na=False)]
    if source:
        data = data[data["source"].str.contains(source, case=False, na=False)]
    total = int(len(data))
    start = (page - 1) * size
    page_rows = data.iloc[start:start + size]
    items = []
    for _, row in page_rows.iterrows():
        items.append({
            "title": row["title"],
            "company": row["company"],
            "location": row["location"],
            "salary_min": float(row["salary_min"] or 0),
            "salary_max": float(row["salary_max"] or 0),
            "salary_mid": float(row["salary_mid"] or 0),
            "level": row["level"],
            "source": row["source"],
            "posted_date": row["posted_date"],
        })
    return {"total": total, "page": page, "size": size, "items": items}


@app.get("/api/sources")
def get_sources():
    jobs, _ = load_frames()
    if jobs is None:
        return {"items": []}
    grouped = jobs.groupby("source").size().reset_index(name="total")
    return {"items": grouped.sort_values("total", ascending=False).to_dict("records")}


@app.get("/api/skills")
def get_skills(limit: int = 20):
    _, skills = load_frames()
    if skills is None:
        return {"items": []}
    top = analysis.top_skills(skills, limit)
    return {"items": top.to_dict("records")}


@app.get("/api/analysis")
def get_analysis():
    jobs, skills = load_frames()
    if jobs is None:
        return {"top_skills": [], "salary_by_role": [], "location": [], "experience": [], "skill_value": []}
    return {
        "top_skills": analysis.top_skills(skills, 20).to_dict("records"),
        "salary_by_role": analysis.salary_by_role(jobs).to_dict("records"),
        "location": analysis.location_distribution(jobs).to_dict("records"),
        "experience": analysis.experience_distribution(jobs).to_dict("records"),
        "skill_value": analysis.skill_value(skills, 15).to_dict("records"),
    }


@app.post("/api/advisor")
def post_advisor(payload: AdvisorInput):
    _, skills = load_frames()
    skill_value_df = analysis.skill_value(skills, 30) if skills is not None else None
    return recommender.analyze_career_ai(
        skills_user=payload.skills,
        level_user=payload.level,
        target_role=payload.target_role,
        expected_salary=payload.expected_salary,
        skill_value_df=skill_value_df,
    )


@app.post("/api/recommendations")
def post_recommendations(payload: AdvisorInput):
    return post_advisor(payload)


@app.get("/api/ai/similar-jobs/{job_id}")
def get_similar_jobs(job_id: int, top_k: int = 5):
    try:
        return {"items": recommend_similar_jobs(DB_PATH, job_id, top_k)}
    except ValueError as error:
        return {"items": [], "error": str(error)}


@app.post("/api/ai/match-profile")
def post_match_profile(payload: ProfileQuery):
    try:
        return {"items": recommend_by_profile(DB_PATH, payload.profile_text, payload.top_k)}
    except Exception as error:
        return {"items": [], "error": str(error)}


@app.get("/api/export/json")
def export_json():
    jobs, _ = load_frames()
    records = [] if jobs is None else jobs.to_dict("records")
    text = json.dumps(records, ensure_ascii=False, indent=2)
    return StreamingResponse(
        io.BytesIO(text.encode("utf-8")),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=jobs.json"},
    )


@app.get("/api/export/csv")
def export_csv():
    jobs, _ = load_frames()
    buffer = io.StringIO()
    fields = ["title", "company", "location", "salary_min", "salary_max", "salary_mid", "level", "source", "posted_date"]
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    if jobs is not None:
        for _, row in jobs.iterrows():
            writer.writerow({key: row[key] for key in fields})
    data = buffer.getvalue().encode("utf-8-sig")
    return StreamingResponse(
        io.BytesIO(data),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=jobs.csv"},
    )
