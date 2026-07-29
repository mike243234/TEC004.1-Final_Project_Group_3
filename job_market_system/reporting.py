import pandas as pd


def df_to_md(df, columns, headers):
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return "\n".join(lines)


def records_to_md(records, columns, headers):
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in records:
        lines.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return "\n".join(lines)


def generate_report(jobs, top_skills_df, salary_role_df, location_df, experience_df, recommendations, gap, charts, output_path):
    parts = []
    parts.append("# Báo cáo phân tích thị trường việc làm IT")
    parts.append("")
    parts.append("Tổng số tin tuyển dụng: {}".format(len(jobs)))
    parts.append("")
    parts.append("## Top kỹ năng được yêu cầu")
    parts.append(df_to_md(top_skills_df.head(15), ["skill", "demand"], ["Kỹ năng", "Số tin"]))
    parts.append("")
    parts.append("## Lương trung vị theo vị trí (triệu VNĐ)")
    parts.append(df_to_md(salary_role_df, ["title", "median_salary"], ["Vị trí", "Lương trung vị"]))
    parts.append("")
    parts.append("## Phân bố theo cấp bậc")
    parts.append(df_to_md(experience_df, ["level", "total"], ["Cấp bậc", "Số tin"]))
    parts.append("")
    parts.append("## Phân bố theo địa điểm")
    parts.append(df_to_md(location_df, ["location", "total"], ["Địa điểm", "Số tin"]))
    parts.append("")
    parts.append("## Gợi ý kỹ năng nên học")
    parts.append(records_to_md(recommendations, ["skill", "demand", "avg_salary", "score"], ["Kỹ năng", "Nhu cầu", "Lương TB", "Điểm"]))
    parts.append("")
    parts.append("## Khoảng cách kỹ năng (nên bổ sung)")
    parts.append(records_to_md(gap, ["skill", "demand", "avg_salary", "score"], ["Kỹ năng", "Nhu cầu", "Lương TB", "Điểm"]))
    parts.append("")
    parts.append("## Biểu đồ")
    for name, path in charts.items():
        parts.append("- {}: {}".format(name, path))
    text = "\n".join(parts)
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return output_path


def generate_weekly_report(jobs, reference_date, output_path):
    data = jobs.copy()
    data["posted_date"] = pd.to_datetime(data["posted_date"], errors="coerce")
    start = pd.Timestamp(reference_date) - pd.Timedelta(days=7)
    end = pd.Timestamp(reference_date)
    recent = data[(data["posted_date"] >= start) & (data["posted_date"] <= end)]
    parts = []
    parts.append("# Báo cáo tuần ({} đến {})".format(start.date(), end.date()))
    parts.append("")
    parts.append("Số tin mới trong tuần: {}".format(len(recent)))
    parts.append("")
    if len(recent) > 0:
        by_location = recent.groupby("location").size().reset_index(name="total").sort_values("total", ascending=False)
        parts.append("## Tin mới theo địa điểm")
        parts.append(df_to_md(by_location, ["location", "total"], ["Địa điểm", "Số tin"]))
    text = "\n".join(parts)
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return output_path
