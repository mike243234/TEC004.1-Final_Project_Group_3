from models import Job, Company, SkillRequirement
from extractor import parse_salary, parse_experience, clean_skill, experience_level, extract_skills, clean_location


def merge_skills(raw):
    names = [clean_skill(name) for name in raw.get("skills", []) if name]
    title_text = "{} {}".format(raw.get("title", ""), raw.get("description", ""))
    names.extend(extract_skills(title_text))
    unique = []
    seen = set()
    for name in names:
        key = name.lower()
        if name and key not in seen:
            seen.add(key)
            unique.append(name)
    return unique


def build_job(raw):
    title = raw.get("title", "")
    exp_text = raw.get("exp_text", "")
    salary_text = raw.get("salary_text", "")
    location = clean_location(raw.get("location", ""))
    years = parse_experience(exp_text, title)
    level = experience_level(years, title)
    salary_min, salary_max = parse_salary(salary_text, title, level)
    company = Company(raw.get("company", "Unknown"), location)
    skills = [SkillRequirement(name) for name in merge_skills(raw)]
    return Job(
        title=title,
        company=company,
        salary_min=salary_min,
        salary_max=salary_max,
        years_experience=years,
        level=level,
        location=location,
        skills=skills,
        source=raw.get("source", "Unknown"),
        posted_date=raw.get("posted_date", ""),
    )


def build_jobs(raw_jobs):
    jobs = list(map(build_job, raw_jobs))
    seen = set()
    unique = []
    for job in jobs:
        key = (job.title.lower(), job.company.name.lower(), job.source)
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique
