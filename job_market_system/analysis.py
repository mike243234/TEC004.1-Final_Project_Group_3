import sqlite3
import pandas as pd


def salary_mid(low, high):
    values = list(filter(lambda value: value and value > 0, [low, high]))
    if not values:
        return 0.0
    return round(sum(values) / len(values), 1)


def load_jobs(db_path):
    connection = sqlite3.connect(db_path)
    jobs = pd.read_sql_query(
        "SELECT Jobs.id, Jobs.title, Companies.name AS company, Jobs.salary_min, Jobs.salary_max, "
        "Jobs.years_experience, Jobs.level, Jobs.location, Jobs.source, Jobs.posted_date "
        "FROM Jobs JOIN Companies ON Jobs.company_id = Companies.id",
        connection,
    )
    skills = pd.read_sql_query(
        "SELECT Skills.name AS skill, Jobs.title, Jobs.salary_min, Jobs.salary_max, Jobs.location "
        "FROM JobSkills JOIN Skills ON JobSkills.skill_id = Skills.id "
        "JOIN Jobs ON JobSkills.job_id = Jobs.id",
        connection,
    )
    connection.close()
    jobs["salary_mid"] = jobs.apply(lambda row: salary_mid(row["salary_min"], row["salary_max"]), axis=1)
    skills["salary_mid"] = skills.apply(lambda row: salary_mid(row["salary_min"], row["salary_max"]), axis=1)
    return jobs, skills


def top_skills(skills, limit=20):
    counts = skills.groupby("skill").size().reset_index(name="demand")
    return counts.sort_values("demand", ascending=False).head(limit).reset_index(drop=True)


def salary_by_role(jobs):
    paid = jobs[jobs["salary_mid"] > 0]
    if paid.empty:
        paid = jobs
    grouped = paid.groupby("title")["salary_mid"].median().reset_index(name="median_salary")
    return grouped.sort_values("median_salary", ascending=False).head(15).reset_index(drop=True)


def experience_distribution(jobs):
    grouped = jobs.groupby("level").size().reset_index(name="total")
    order_map = {"Entry": 1, "Junior": 2, "Middle": 3, "Senior": 4}
    grouped["rank"] = grouped["level"].map(lambda x: order_map.get(x, 99))
    return grouped.sort_values("rank").drop(columns=["rank"]).reset_index(drop=True)


def location_distribution(jobs):
    counts = jobs.groupby("location").size().reset_index(name="total")
    counts = counts.sort_values("total", ascending=False).reset_index(drop=True)
    if len(counts) > 5:
        top5 = counts.head(5)
        others_total = counts.iloc[5:]["total"].sum()
        if others_total > 0:
            others_df = pd.DataFrame([{"location": "Khác", "total": int(others_total)}])
            return pd.concat([top5, others_df], ignore_index=True)
    return counts


def skill_value(skills, limit=30):
    demand = skills.groupby("skill").size().reset_index(name="demand")
    paid = skills[skills["salary_mid"] > 0]
    if paid.empty:
        grouped = demand.copy()
        grouped["avg_salary"] = 15.0
        grouped["score"] = grouped["demand"].astype(float)
    else:
        avg = paid.groupby("skill")["salary_mid"].mean().reset_index(name="avg_salary")
        grouped = demand.merge(avg, on="skill", how="left").fillna({"avg_salary": 15.0})
        grouped["avg_salary"] = grouped["avg_salary"].round(1)
        grouped["score"] = grouped.apply(
            lambda row: round(row["demand"] * row["avg_salary"], 1),
            axis=1,
        )
    return grouped.sort_values("score", ascending=False).head(limit).reset_index(drop=True)
