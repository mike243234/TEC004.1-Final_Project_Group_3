import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS Companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT
);
CREATE TABLE IF NOT EXISTS Jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company_id INTEGER,
    salary_min REAL,
    salary_max REAL,
    years_experience INTEGER,
    level TEXT,
    location TEXT,
    source TEXT,
    posted_date TEXT,
    FOREIGN KEY (company_id) REFERENCES Companies(id)
);
CREATE TABLE IF NOT EXISTS Skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS JobSkills (
    job_id INTEGER,
    skill_id INTEGER,
    PRIMARY KEY (job_id, skill_id),
    FOREIGN KEY (job_id) REFERENCES Jobs(id),
    FOREIGN KEY (skill_id) REFERENCES Skills(id)
);
"""


class JobDatabase:
    def __init__(self, path):
        self.connection = sqlite3.connect(path)

    def reset(self):
        self.connection.executescript(
            "DROP TABLE IF EXISTS JobSkills;"
            "DROP TABLE IF EXISTS Jobs;"
            "DROP TABLE IF EXISTS Skills;"
            "DROP TABLE IF EXISTS Companies;"
        )
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def get_or_create_company(self, company):
        cursor = self.connection.execute(
            "SELECT id FROM Companies WHERE name = ? AND location = ?",
            (company.name, company.location),
        )
        row = cursor.fetchone()
        if row:
            return row[0]
        cursor = self.connection.execute(
            "INSERT INTO Companies (name, location) VALUES (?, ?)",
            (company.name, company.location),
        )
        return cursor.lastrowid

    def get_or_create_skill(self, name):
        cursor = self.connection.execute("SELECT id FROM Skills WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return row[0]
        cursor = self.connection.execute("INSERT INTO Skills (name) VALUES (?)", (name,))
        return cursor.lastrowid

    def insert_job(self, job):
        company_id = self.get_or_create_company(job.company)
        cursor = self.connection.execute(
            "INSERT INTO Jobs (title, company_id, salary_min, salary_max, years_experience, level, location, source, posted_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (job.title, company_id, job.salary_min, job.salary_max, job.years_experience, job.level, job.location, job.source, job.posted_date),
        )
        job_id = cursor.lastrowid
        for skill in job.skills:
            skill_id = self.get_or_create_skill(skill.name)
            self.connection.execute(
                "INSERT OR IGNORE INTO JobSkills (job_id, skill_id) VALUES (?, ?)",
                (job_id, skill_id),
            )

    def save_all(self, jobs):
        for job in jobs:
            self.insert_job(job)
        self.connection.commit()

    def top_skills(self, limit=20):
        query = (
            "SELECT Skills.name, COUNT(JobSkills.job_id) AS demand "
            "FROM Skills JOIN JobSkills ON Skills.id = JobSkills.skill_id "
            "GROUP BY Skills.name ORDER BY demand DESC LIMIT ?"
        )
        return self.connection.execute(query, (limit,)).fetchall()

    def salary_by_level(self):
        query = (
            "SELECT level, ROUND(AVG((salary_min + salary_max) / 2.0), 1) AS avg_salary, COUNT(*) AS total "
            "FROM Jobs WHERE salary_max > 0 GROUP BY level ORDER BY avg_salary"
        )
        return self.connection.execute(query).fetchall()

    def jobs_by_location(self):
        query = "SELECT location, COUNT(*) AS total FROM Jobs GROUP BY location ORDER BY total DESC"
        return self.connection.execute(query).fetchall()

    def close(self):
        self.connection.close()
