import pandas as pd

try:
    from ai.advisor_llm import generate_advice_llm, AdvisorLLMUnavailable
except ImportError:
    generate_advice_llm = None
    AdvisorLLMUnavailable = Exception


def recommend_skills(skill_value_df, limit=10):
    records = skill_value_df.head(limit).to_dict("records")
    return list(map(lambda row: {
        "skill": row["skill"],
        "demand": int(row["demand"]),
        "avg_salary": round(row["avg_salary"], 1),
        "score": round(row["score"], 1),
    }, records))


def skill_gap(skill_value_df, student_skills, limit=10):
    owned = set(skill.strip().lower() for skill in student_skills)
    records = skill_value_df.to_dict("records")
    missing = filter(lambda row: row["skill"].lower() not in owned, records)
    ranked = sorted(missing, key=lambda row: row["score"], reverse=True)
    return list(map(lambda row: {
        "skill": row["skill"],
        "demand": int(row["demand"]),
        "avg_salary": round(row["avg_salary"], 1),
        "score": round(row["score"], 1),
    }, ranked[:limit]))


def _template_advice(match_score, best_role, level_user, matched_skills, missing_skills, market_salary_range, expected_salary):
    """Original deterministic template. Kept as a fallback so /api/advisor
    still works on a machine that hasn't set up Ollama -- e.g. a grader
    running the project without following the AI setup steps."""
    advice_parts = []
    advice_parts.append(f"### 🎯 Đánh giá mức độ phù hợp: {match_score}%")
    advice_parts.append(f"Dựa trên các kỹ năng hiện có và phân tích dữ liệu tuyển dụng thực tế, vai trò phù hợp nhất dành cho bạn là **{best_role}** ({level_user}).")
    advice_parts.append("")
    advice_parts.append("### 💪 Kỹ năng thế mạnh đã đáp ứng:")
    if matched_skills:
        advice_parts.append(f"- **{', '.join(matched_skills)}** (Các công nghệ then chốt có nhu cầu cao trên thị trường).")
    else:
        advice_parts.append("- Bạn cần bổ sung thêm các kỹ năng nền tảng cốt lõi của ngành IT.")

    advice_parts.append("")
    advice_parts.append("### 🚀 Kỹ năng nên bổ sung để tăng cạnh tranh:")
    if missing_skills:
        advice_parts.append(f"- **{', '.join(missing_skills[:5])}**.")

    advice_parts.append("")
    advice_parts.append(f"### 💰 Mức lương thị trường dự báo ({level_user} - {best_role}):")
    advice_parts.append(f"- Khoảng lương phổ biến: **{market_salary_range[0]} - {market_salary_range[1]} triệu VNĐ/tháng**.")
    if expected_salary > market_salary_range[1]:
        advice_parts.append(f"- Mức kỳ vọng ({expected_salary} triệu) của bạn cao hơn mặt bằng chung. Cần nâng cao kỹ năng Cloud, AI hoặc hệ thống lớn để đạt được.")
    else:
        advice_parts.append(f"- Mức kỳ vọng ({expected_salary} triệu) nằm trong tầm tay với hồ sơ năng lực hiện tại.")

    advice_parts.append("")
    advice_parts.append("### 📅 Lộ trình phát triển 3 tháng đề xuất:")
    p1 = matched_skills[0] if matched_skills else "Python/JavaScript"
    p2 = missing_skills[0] if missing_skills else "Docker/AWS"
    advice_parts.append(f"1. **Tháng 1**: Xây dựng dự án thực tế với **{p1}** & thiết kế REST API.")
    advice_parts.append(f"2. **Tháng 2**: Thực hành quy trình CI/CD và đóng gói ứng dụng với **{p2}**.")
    advice_parts.append("3. **Tháng 3**: Chuẩn bị Portfolio GitHub, luyện tập phỏng vấn thuật toán & System Design.")
    return "\n".join(advice_parts)


def analyze_career_ai(skills_user, level_user="Junior", target_role="Fullstack", expected_salary=20.0, skill_value_df=None):
    user_skills_clean = [s.strip() for s in skills_user if s and s.strip()]
    user_set = set(s.lower() for s in user_skills_clean)

    if skill_value_df is None or skill_value_df.empty:
        top_market_skills = ["Python", "Java", "React", "Node.js", "SQL", "AWS", "Docker", "TypeScript", "JavaScript"]
    else:
        top_market_skills = skill_value_df["skill"].tolist()[:15]

    matched_skills = [s for s in top_market_skills if s.lower() in user_set]
    missing_skills = [s for s in top_market_skills if s.lower() not in user_set]

    total_check = max(len(top_market_skills), 1)
    matched_count = len(matched_skills)
    match_score = min(100, int((matched_count / min(8, total_check)) * 75 + (5 if user_skills_clean else 0) + 15))

    role_map = {
        "Backend": ["Python", "Java", "Node.js", "SQL", "Go", "Docker", "API", "Spring"],
        "Frontend": ["JavaScript", "TypeScript", "React", "Vue.js", "HTML", "CSS", "Next.js"],
        "Fullstack": ["JavaScript", "React", "Node.js", "Python", "SQL", "API", "TypeScript"],
        "Data & AI": ["Python", "SQL", "Data Engineering", "AI", "Machine Learning", "AWS", "Spark"],
        "DevOps": ["Docker", "Kubernetes", "AWS", "CI/CD", "Linux", "DevOps", "Python"],
        "QA / QC": ["Testing", "Automation Testing", "QA/QC", "API", "Python", "SQL"]
    }

    role_scores = {}
    for role_name, req_skills in role_map.items():
        score = sum(1 for rs in req_skills if rs.lower() in user_set)
        role_scores[role_name] = score

    sorted_roles = sorted(role_scores.items(), key=lambda x: x[1], reverse=True)
    best_role = sorted_roles[0][0] if sorted_roles[0][1] > 0 else (target_role or "Fullstack Developer")

    salary_benchmarks = {
        "Entry": (8.0, 15.0),
        "Junior": (14.0, 22.0),
        "Middle": (22.0, 35.0),
        "Senior": (35.0, 65.0)
    }
    market_salary_range = salary_benchmarks.get(level_user, (15.0, 28.0))

    if generate_advice_llm is not None:
        try:
            ai_advice_text = generate_advice_llm(
                match_score=match_score,
                best_role=best_role,
                level_user=level_user,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                salary_min=market_salary_range[0],
                salary_max=market_salary_range[1],
                expected_salary=expected_salary,
            )
        except AdvisorLLMUnavailable:
            ai_advice_text = _template_advice(match_score, best_role, level_user, matched_skills, missing_skills, market_salary_range, expected_salary)
    else:
        ai_advice_text = _template_advice(match_score, best_role, level_user, matched_skills, missing_skills, market_salary_range, expected_salary)

    gap_items = []
    if skill_value_df is not None and not skill_value_df.empty:
        gap_items = skill_gap(skill_value_df, user_skills_clean, 8)
    else:
        gap_items = [{"skill": s, "demand": 15, "avg_salary": 25.0, "score": 375.0} for s in missing_skills[:8]]

    return {
        "match_score": match_score,
        "best_role": best_role,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills[:8],
        "salary_min": market_salary_range[0],
        "salary_max": market_salary_range[1],
        "ai_advice": ai_advice_text,
        "gap": gap_items
    }
