"""
ai/embeddings.py
-----------------
Turns each job posting into a numeric vector ("embedding") built from its
title, level, location, and skill list, so jobs can be ranked by
*meaning* instead of exact string matching. This is what powers real
semantic recommendation -- something recommender.skill_gap() can't do,
since it only matches skill names that are spelled identically.

TERMS, PLAIN-ENGLISH VERSION:
  - Embedding: a list of ~384 numbers representing what a piece of text
    is about. "Backend developer, skills: Node.js, MongoDB" and
    "server-side engineer, skills: Express, databases" end up numerically
    close, even sharing zero exact words.
  - Cosine similarity: a score from -1 to 1 for how closely two
    embeddings point in the same direction. 1 = same meaning, 0 =
    unrelated. Vectors here are length-normalized, so cosine similarity
    is just a dot product -- that's why the code below can do
    `vectors @ query_vec` instead of a longer formula.

WHY BUILT FROM STRUCTURED FIELDS, NOT RAW DESCRIPTION TEXT:
Your pipeline discards the raw scraped description after extractor.py
pulls structured fields out of it (see processing.merge_skills) -- only
title/skills/level/location/salary reach the Jobs table. Rather than
change the scraping/storage pipeline this late, this module builds
embedding text straight from those structured fields, e.g.:
    "Backend Developer. Level: Senior. Location: Hà Nội.
     Skills: Python, Django, PostgreSQL, Docker."
That's a clean, information-dense input for a sentence embedding model --
arguably cleaner than raw HTML description text would have been.

MODEL: sentence-transformers/all-MiniLM-L6-v2 -- free, ~80MB, downloads
once then runs fully offline.

SETUP:  pip install sentence-transformers numpy --break-system-packages
"""

import sqlite3
from typing import List, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None  # lazy-loaded singleton so the model only loads once per process

SCHEMA_AI = """
CREATE TABLE IF NOT EXISTS job_embeddings (
    job_id INTEGER PRIMARY KEY,
    embedding BLOB NOT NULL,
    model_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES Jobs(id)
);
"""


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_text(text: str) -> np.ndarray:
    # normalize_embeddings=True makes cosine similarity == a plain dot
    # product, which is much cheaper to compute across hundreds of jobs.
    return get_model().encode(text, normalize_embeddings=True)


def _job_text(title: str, level: str, location: str, skills: str) -> str:
    return f"{title}. Level: {level}. Location: {location}. Skills: {skills}."


def rebuild_embeddings(db_path: str) -> int:
    """Recompute embeddings for every job currently in the database.

    Your JobDatabase.reset() drops and recreates the Jobs table on every
    scrape (see database.py / api.rebuild_database), which means job ids
    are reused from 1 each time. A stale job_embeddings row from a
    previous scrape would silently point at the wrong job after that --
    so this does a full DELETE + rebuild rather than an incremental
    backfill. For ~500 jobs this takes a few seconds on CPU, so it's not
    worth optimizing to incremental for a project this size.

    Call this right after database.save_all(jobs) in api.rebuild_database
    (or after main.py's equivalent step) so embeddings stay in sync with
    whatever the latest scrape produced.
    """
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA_AI)
        conn.execute("DELETE FROM job_embeddings")

        rows = conn.execute(
            """SELECT Jobs.id, Jobs.title, Jobs.level, Jobs.location,
                      COALESCE(GROUP_CONCAT(Skills.name, ', '), '') AS skills
               FROM Jobs
               LEFT JOIN JobSkills ON JobSkills.job_id = Jobs.id
               LEFT JOIN Skills ON Skills.id = JobSkills.skill_id
               GROUP BY Jobs.id"""
        ).fetchall()

        count = 0
        for job_id, title, level, location, skills in rows:
            text = _job_text(title, level or "", location or "", skills)
            vector = embed_text(text).astype(np.float32).tobytes()
            conn.execute(
                "INSERT INTO job_embeddings (job_id, embedding, model_name) VALUES (?, ?, ?)",
                (job_id, vector, MODEL_NAME),
            )
            count += 1
        conn.commit()
    return count


def _load_all_embeddings(db_path: str) -> Tuple[List[int], np.ndarray]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT job_id, embedding FROM job_embeddings").fetchall()
    ids = [r[0] for r in rows]
    vectors = np.array([np.frombuffer(r[1], dtype=np.float32) for r in rows])
    return ids, vectors


def _hydrate(db_path: str, ranked: List[Tuple[int, float]]) -> List[dict]:
    """Attach title/company/location/salary to each (job_id, score) pair
    so the API can return something directly usable by the frontend."""
    if not ranked:
        return []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        placeholders = ", ".join("?" * len(ranked))
        rows = conn.execute(
            f"""SELECT Jobs.id, Jobs.title, Companies.name AS company, Jobs.location,
                       Jobs.level, Jobs.salary_min, Jobs.salary_max
                FROM Jobs JOIN Companies ON Jobs.company_id = Companies.id
                WHERE Jobs.id IN ({placeholders})""",
            [job_id for job_id, _ in ranked],
        ).fetchall()
    by_id = {row["id"]: dict(row) for row in rows}
    results = []
    for job_id, score in ranked:
        if job_id not in by_id:
            continue
        item = by_id[job_id]
        item["job_id"] = item.pop("id")
        item["score"] = round(score, 4)
        results.append(item)
    return results


def recommend_similar_jobs(db_path: str, job_id: int, top_k: int = 5) -> List[dict]:
    """'Jobs similar to this one' -- ranked by how close their embeddings
    are to the given job's embedding."""
    ids, vectors = _load_all_embeddings(db_path)
    if job_id not in ids:
        raise ValueError(f"No embedding stored for job_id={job_id}. Run rebuild_embeddings() first.")
    idx = ids.index(job_id)
    similarities = vectors @ vectors[idx]
    ranked = sorted(
        ((ids[i], float(similarities[i])) for i in range(len(ids)) if ids[i] != job_id),
        key=lambda pair: pair[1],
        reverse=True,
    )[:top_k]
    return _hydrate(db_path, ranked)


def recommend_by_profile(db_path: str, profile_text: str, top_k: int = 10) -> List[dict]:
    """The richer alternative to skill_gap(): instead of a fixed list of
    skill names, the user pastes free text describing their background
    or goals (e.g. 'Sinh vien nam 3, biet Python va SQL, muon lam ve du
    lieu'), and jobs are ranked by semantic relevance to that text."""
    ids, vectors = _load_all_embeddings(db_path)
    query_vec = embed_text(profile_text)
    similarities = vectors @ query_vec
    ranked = sorted(zip(ids, similarities.tolist()), key=lambda pair: pair[1], reverse=True)[:top_k]
    return _hydrate(db_path, ranked)
