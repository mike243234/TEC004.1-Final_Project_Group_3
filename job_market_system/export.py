import csv
import json


def export_json(jobs, path):
    # Chuyển đổi dữ liệu object sang dict[cite: 1]
    data = [job.to_dict() for job in jobs] if hasattr(jobs[0], 'to_dict') else jobs
    
    # Đổi encoding sang utf-8-sig để fix lỗi kí tự[cite: 1]
    with open(path, "w", encoding="utf-8-sig") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    return path


def export_csv(jobs, path):
    fields = [
        "title", "company", "location", "salary_min", "salary_max",
        "salary_midpoint", "years_experience", "level", "skills", "source", "posted_date"
    ]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for job in jobs:
            company_name = job.company.name if hasattr(job.company, "name") else str(job.company)
            skills_str = ", ".join(skill.name for skill in job.skills) if hasattr(job, "skills") and isinstance(job.skills, list) else str(getattr(job, "skills", ""))
            writer.writerow({
                "title": job.title,
                "company": company_name,
                "location": job.location,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "salary_midpoint": job.salary_midpoint(),
                "years_experience": job.years_experience,
                "level": job.level,
                "skills": skills_str,
                "source": job.source,
                "posted_date": job.posted_date,
            })
    return path
