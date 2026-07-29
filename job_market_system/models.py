class Record:
    def to_dict(self):
        return dict(self.__dict__)


class SkillRequirement(Record):
    def __init__(self, name, level="any"):
        self.name = name
        self.level = level


class Company(Record):
    def __init__(self, name, location):
        self.name = name
        self.location = location


class Job(Record):
    def __init__(self, title, company, salary_min, salary_max, years_experience, level, location, skills, source, posted_date):
        self.title = title
        self.company = company
        self.salary_min = salary_min
        self.salary_max = salary_max
        self.years_experience = years_experience
        self.level = level
        self.location = location
        self.skills = skills
        self.source = source
        self.posted_date = posted_date

    def salary_midpoint(self):
        values = list(filter(lambda value: value > 0, [self.salary_min, self.salary_max]))
        if not values:
            return 0.0
        return round(sum(values) / len(values), 1)

    def to_dict(self):
        company_val = self.company.to_dict() if hasattr(self.company, "to_dict") else str(self.company)
        skills_val = [skill.name for skill in self.skills] if isinstance(self.skills, list) else []
        return {
            "title": self.title,
            "company": company_val,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_midpoint": self.salary_midpoint(),
            "years_experience": self.years_experience,
            "level": self.level,
            "location": self.location,
            "skills": skills_val,
            "source": self.source,
            "posted_date": self.posted_date,
        }
