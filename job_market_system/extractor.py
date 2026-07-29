import re

SKILL_ALIASES = {
    "reactjs": "React",
    "react.js": "React",
    "react": "React",
    "nodejs": "Node.js",
    "node js": "Node.js",
    "node.js": "Node.js",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "sql": "SQL",
    "aws": "AWS",
    "html": "HTML",
    "css": "CSS",
    "ci/cd": "CI/CD",
    "power bi": "Power BI",
    "machine learning": "Machine Learning",
    "manual testing": "Manual Testing",
    "api testing": "API",
    "api": "API",
    "rest api": "API",
    "ai": "AI",
    "devops": "DevOps",
    "nlp": "NLP",
    "ui/ux": "UI/UX",
    "ui ux": "UI/UX",
    "qa qc": "QA/QC",
    "qa/qc": "QA/QC",
    "tester": "Testing",
    "testing": "Testing",
    "golang": "Go",
    "go": "Go",
    ".net": ".NET",
    "c#": "C#",
    "c++": "C++",
    "data engineer": "Data Engineering",
    "data engineering": "Data Engineering",
    "data analyst": "Data Analysis",
    "data analysis": "Data Analysis",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
    "nextjs": "Next.js",
    "next.js": "Next.js",
}

SKILL_KEYWORDS = [
    ("javascript", "JavaScript"),
    ("typescript", "TypeScript"),
    ("reactjs", "React"),
    ("react native", "React Native"),
    ("react", "React"),
    ("angular", "Angular"),
    ("vue.js", "Vue.js"),
    ("vuejs", "Vue.js"),
    ("vue", "Vue.js"),
    ("next.js", "Next.js"),
    ("nextjs", "Next.js"),
    ("node.js", "Node.js"),
    ("nodejs", "Node.js"),
    ("express", "Express"),
    ("python", "Python"),
    ("django", "Django"),
    ("flask", "Flask"),
    ("fastapi", "FastAPI"),
    ("java", "Java"),
    ("spring", "Spring"),
    ("kotlin", "Kotlin"),
    ("php", "PHP"),
    ("laravel", "Laravel"),
    ("golang", "Go"),
    ("ruby", "Ruby"),
    ("rust", "Rust"),
    ("scala", "Scala"),
    ("swift", "Swift"),
    ("objective-c", "Objective-C"),
    ("flutter", "Flutter"),
    ("dart", "Dart"),
    (".net", ".NET"),
    ("asp.net", ".NET"),
    ("c#", "C#"),
    ("c++", "C++"),
    ("html", "HTML"),
    ("css", "CSS"),
    ("tailwind", "Tailwind"),
    ("bootstrap", "Bootstrap"),
    ("sql server", "SQL Server"),
    ("mysql", "MySQL"),
    ("postgresql", "PostgreSQL"),
    ("postgres", "PostgreSQL"),
    ("mongodb", "MongoDB"),
    ("redis", "Redis"),
    ("oracle", "Oracle"),
    ("elasticsearch", "Elasticsearch"),
    ("sql", "SQL"),
    ("aws", "AWS"),
    ("azure", "Azure"),
    ("gcp", "GCP"),
    ("google cloud", "GCP"),
    ("docker", "Docker"),
    ("kubernetes", "Kubernetes"),
    ("terraform", "Terraform"),
    ("jenkins", "Jenkins"),
    ("ci/cd", "CI/CD"),
    ("devops", "DevOps"),
    ("linux", "Linux"),
    ("git", "Git"),
    ("graphql", "GraphQL"),
    ("rest api", "API"),
    ("api", "API"),
    ("microservices", "Microservices"),
    ("machine learning", "Machine Learning"),
    ("deep learning", "Deep Learning"),
    ("data science", "Data Science"),
    ("data engineering", "Data Engineering"),
    ("data engineer", "Data Engineering"),
    ("data analysis", "Data Analysis"),
    ("data analyst", "Data Analysis"),
    ("big data", "Big Data"),
    ("spark", "Spark"),
    ("hadoop", "Hadoop"),
    ("airflow", "Airflow"),
    ("power bi", "Power BI"),
    ("tableau", "Tableau"),
    ("pandas", "Pandas"),
    ("tensorflow", "TensorFlow"),
    ("pytorch", "PyTorch"),
    ("nlp", "NLP"),
    ("computer vision", "Computer Vision"),
    ("ai", "AI"),
    ("manual testing", "Manual Testing"),
    ("automation test", "Automation Testing"),
    ("automation testing", "Automation Testing"),
    ("api testing", "API"),
    ("tester", "Testing"),
    ("qa qc", "QA/QC"),
    ("qa/qc", "QA/QC"),
    ("figma", "Figma"),
    ("ui/ux", "UI/UX"),
    ("ux/ui", "UI/UX"),
    ("agile", "Agile"),
    ("scrum", "Scrum"),
    ("english", "English"),
    ("japanese", "Japanese"),
    ("korean", "Korean"),
]

SPECIAL_TOKENS = {".net", "c#", "c++", "ci/cd", "ui/ux", "ux/ui", "node.js", "next.js", "react.js", "asp.net", "objective-c", "vue.js", "qa/qc"}


def clean_skill(name):
    key = name.strip().lower()
    if key in SKILL_ALIASES:
        return SKILL_ALIASES[key]
    return name.strip().title()


def extract_skills(text):
    if not text:
        return []
    lowered = " " + text.lower() + " "
    found = []
    for token, canonical in SKILL_KEYWORDS:
        if token in SPECIAL_TOKENS:
            matched = token in lowered
        else:
            matched = re.search(r"(?<![a-z0-9])" + re.escape(token) + r"(?![a-z0-9])", lowered) is not None
        if matched and canonical not in found:
            found.append(canonical)
    return found


def clean_location(text):
    if not text:
        return "Hồ Chí Minh"
    low = text.lower().strip()
    if any(k in low for k in ["hồ chí minh", "ho chi minh", "hcm", "tphcm", "saigon", "sài gòn"]):
        return "Hồ Chí Minh"
    if any(k in low for k in ["hà nội", "ha noi", "hn"]):
        return "Hà Nội"
    if any(k in low for k in ["đà nẵng", "da nang", "dn"]):
        return "Đà Nẵng"
    if "bình dương" in low:
        return "Bình Dương"
    if "đồng nai" in low:
        return "Đồng Nai"
    if "bắc ninh" in low:
        return "Bắc Ninh"
    if "hải phòng" in low:
        return "Hải Phòng"
    if "cần thơ" in low:
        return "Cần Thơ"
    return "Khác"


def estimate_salary_by_role(title, level):
    title_low = title.lower()
    lvl = level.lower()
    
    if any(w in title_low for w in ["director", "head", "principal", "cto", "giám đốc"]):
        base = (50.0, 90.0)
    elif any(w in title_low for w in ["lead", "architect", "manager", "trưởng phòng"]):
        base = (35.0, 65.0)
    elif lvl == "senior" or any(w in title_low for w in ["senior", "sr"]):
        base = (25.0, 45.0)
    elif lvl == "middle" or any(w in title_low for w in ["middle", "mid"]):
        base = (18.0, 30.0)
    elif lvl == "junior" or any(w in title_low for w in ["junior", "jr"]):
        base = (12.0, 20.0)
    elif lvl == "entry" or any(w in title_low for w in ["fresher", "intern", "thực tập"]):
        base = (6.0, 12.0)
    else:
        base = (18.0, 32.0)

    if any(w in title_low for w in ["ai", "machine learning", "data engineer", "devops", "cloud"]):
        base = (round(base[0] * 1.15, 1), round(base[1] * 1.15, 1))

    return base


def parse_salary(text, title="", level=""):
    if not text:
        return estimate_salary_by_role(title, level)
    lowered = text.lower().strip()
    if any(word in lowered for word in ["thỏa thuận", "thoa thuan", "thương lượng", "thuong luong", "cạnh tranh", "canh tranh", "nego", "sign in"]):
        return estimate_salary_by_role(title, level)
    
    if "usd" in lowered or "$" in lowered:
        cleaned = lowered.replace(",", "")
        numbers = [int(item) for item in re.findall(r"\d+", cleaned)]
        values = [round(number * 25.0 / 1000.0, 1) for number in numbers]
    elif any(k in lowered for k in ["triệu", "trieu", "tr/tháng", "tr/thang", "tr"]):
        numbers = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", lowered)]
        values = numbers
    elif "vnd" in lowered or "đồng" in lowered:
        cleaned = lowered.replace(".", "").replace(",", "")
        numbers = [int(item) for item in re.findall(r"\d+", cleaned)]
        values = [round(number / 1000000.0, 1) for number in numbers]
    else:
        numbers = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", lowered)]
        values = numbers

    if not values:
        return estimate_salary_by_role(title, level)
    
    if len(values) == 1:
        val = values[0]
        if val > 1000:
            val = round(val / 1000000.0, 1)
        if val <= 0:
            return estimate_salary_by_role(title, level)
        if "up to" in lowered or "đến" in lowered or "den" in lowered:
            return (round(val * 0.7, 1), round(val, 1))
        if "from" in lowered or "trên" in lowered or "từ" in lowered or "tu" in lowered:
            return (round(val, 1), round(val * 1.3, 1))
        return (round(val * 0.85, 1), round(val * 1.15, 1))
        
    s_min, s_max = min(values), max(values)
    if s_min > 1000:
        s_min = round(s_min / 1000000.0, 1)
        s_max = round(s_max / 1000000.0, 1)
    if s_min <= 0 or s_max <= 0:
        return estimate_salary_by_role(title, level)
    return (round(s_min, 1), round(s_max, 1))


def parse_experience(text, title=""):
    combined = (title + " " + text).lower()
    
    if any(w in combined for w in ["fresher", "intern", "thực tập", "thuc tap", "trainee", "entry", "mới tốt nghiệp", "moi tot nghiep", "young talent", "không yêu cầu", "khong yeu cau", "dưới 1", "duoi 1", "không cần", "khong can"]):
        return 0
        
    match = re.search(r"(\d+)\s*(?:-\s*\d+)?\s*(?:năm|nam|years|year|yoe)", combined)
    if match:
        return int(match.group(1))

    if any(w in combined for w in ["principal", "director", "architect", "head"]):
        return 7
    if any(w in combined for w in ["lead", "manager", "trưởng phòng", "chuyên gia"]):
        return 5
    if any(w in combined for w in ["senior", "sr.", "sr"]):
        return 4
    if any(w in combined for w in ["middle", "mid", "chuyên viên"]):
        return 3
    if any(w in combined for w in ["junior", "jr.", "jr"]):
        return 1

    return 2


def experience_level(years, title=""):
    title_low = title.lower()
    if any(w in title_low for w in ["senior", "sr", "lead", "architect", "principal", "manager", "director", "expert"]):
        return "Senior"
    if any(w in title_low for w in ["middle", "mid"]):
        return "Middle"
    if any(w in title_low for w in ["junior", "jr"]):
        return "Junior"
    if any(w in title_low for w in ["fresher", "intern", "thực tập", "entry", "trainee"]):
        return "Entry"

    if years <= 0:
        return "Entry"
    if years <= 2:
        return "Junior"
    if years <= 4:
        return "Middle"
    return "Senior"
